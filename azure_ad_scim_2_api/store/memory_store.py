import uuid
from typing import Dict, List

from scim2_filter_parser import ast
from scim2_filter_parser.ast import LogExpr, Filter, AttrExpr, CompValue, AttrPath, AST
from scim2_filter_parser.parser import SCIMParser
from scim2_filter_parser.lexer import SCIMLexer

from azure_ad_scim_2_api.store import BaseStore
from azure_ad_scim_2_api.util.case_insensitive_dict import CaseInsensitiveDict
from azure_ad_scim_2_api.util.exc import ResourceNotFound, ResourceAlreadyExists


def _norm_lst(lst: List, attr: str = "value") -> List:
    if attr:
        lst = [it.get(attr) for it in lst]
    return lst


def eq_in_list(lst: List, predicate: str, attr: str = "value"):
    return predicate in _norm_lst(lst, attr)


def ne_in_list(lst: List, predicate: str, attr: str = "value"):
    return predicate not in _norm_lst(lst, attr)


def co_in_list(lst: List, predicate: str, attr: str = "value"):
    for it in _norm_lst(lst, attr):
        if it.lower().__contains__(predicate.lower()):
            return True
    return False


def sw_in_list(lst: List, predicate: str, attr: str = "value"):
    for it in _norm_lst(lst, attr):
        if it.lower().startswith(predicate.lower()):
            return True
    return False


def ew_in_list(lst: List, predicate: str, attr: str = "value"):
    for it in _norm_lst(lst, attr):
        if it.lower().endswith(predicate.lower()):
            return True
    return False


class MemoryStore(BaseStore):
    resource_db: Dict = {}
    iterable_attributes = ["emails", "groups"]

    def __init__(self):
        self.resource_db = {}

    filter_map = {
        "eq": lambda a, b: str(a).lower().__eq__(str(b).lower()),
        "ne": lambda a, b: str(a).lower().__ne__(str(b).lower()),
        "co": lambda a, b: a.lower().__contains__(b.lower()),
        "sw": lambda a, b: str(a).lower().startswith(str(b).lower()),
        "ew": lambda a, b: str(a).lower().endswith(str(b).lower()),
        "gt": lambda a, b: a > b,
        "ge": lambda a, b: a >= b,
        "lt": lambda a, b: a < b,
        "le": lambda a, b: a <= b,
        "pr": lambda a, b: a is not None,
        "eq_lst": eq_in_list,
        "ne_lst": ne_in_list,
        "co_lst": co_in_list,
        "sw_lst": sw_in_list,
        "ew_lst": ew_in_list,
    }

    async def search(self, _filter: str, start_index: int = 1, count: int = 100) -> tuple[list[Dict], int]:
        if not _filter:
            res = list(self.resource_db.values())
        else:
            pf = await self.parse_filter_expression(_filter)
            res = [
                r for r in self.resource_db.values()
                if await self.evaluate_filter(pf, await CaseInsensitiveDict.build_deep(r))
            ]
        total_results = len(res)
        paginated = res[start_index - 1: start_index - 1 + count:]
        return paginated, total_results

    async def update(self, resource_id: str, **kwargs: Dict) -> Dict:
        if resource_id not in self.resource_db:
            raise ResourceNotFound("User", resource_id)

        resource = self.resource_db.get(resource_id)
        resource.update(await self._sanitize(kwargs))
        self.resource_db[resource_id] = resource
        return resource

    async def create(self, resource: Dict) -> Dict:
        resource_id = resource.get("id")
        if resource_id and resource_id in self.resource_db:
            raise ResourceAlreadyExists("User", resource_id)
        resource_id = resource_id or str(uuid.uuid4())
        resource["id"] = resource_id
        self.resource_db[resource_id] = await self._sanitize(resource)
        return resource

    async def delete(self, resource_id: str) -> None:
        if resource_id not in self.resource_db:
            raise ResourceNotFound("User", resource_id)
        del self.resource_db[resource_id]
        return

    async def get_by_id(self, resource_id: str) -> Dict:
        if resource_id not in self.resource_db:
            raise ResourceNotFound("User", resource_id)

        return await self._sanitize(self.resource_db.get(resource_id))

    async def parse_filter_expression(self, expr: str) -> Dict:
        token_stream = SCIMLexer().tokenize(expr)
        ast_nodes = SCIMParser().parse(token_stream)
        # We only need the root node, which contains all the references in the tree for traversal:
        _, root = ast.flatten(ast_nodes)[0]
        return await self.parse_scim_filter(root)

    async def evaluate_filter(self, parsed_filter: Dict, node: Dict):
        negated = parsed_filter.get("negated", False)
        expr = parsed_filter.get("expr")
        f = expr.get("func")
        if f:
            f = expr["func"]
            pred = expr["pred"]
            attr = expr["attr"].lower()
            op = expr["op"].lower()
            attr_parts = attr.split(".")
            node_attr_value = node
            namespace = expr.get("namespace")
            if namespace:
                f = self.filter_map[f"{op}_lst"]
                lst = node.get(namespace)
                return not \
                    f(lst, pred, attr) if negated \
                    else f(lst, pred, attr)
            if type(node_attr_value.get(attr_parts[0])) == list:
                f = self.filter_map[f"{op}_lst"]
                deep_attribute = attr_parts[-1]
                lst_attr = node_attr_value.get(attr_parts[0])
                if deep_attribute != attr_parts[0] and type(deep_attribute) != list:
                    return not \
                        f(lst_attr, pred, deep_attribute) if negated \
                        else f(lst_attr, pred, deep_attribute)
                return not \
                    f(lst_attr, pred) if negated \
                    else f(lst_attr, pred)
            else:
                for ap in attr_parts:
                    node_attr_value = node_attr_value.get(ap)
                    if not node_attr_value:
                        break

            return not f(node_attr_value, pred) if negated else f(node_attr_value, pred)
        if "and" in expr:
            res = await self.evaluate_filter(expr["and"][0], node) and \
                  await self.evaluate_filter(expr["and"][1], node)
        elif "or" in expr:
            res = await self.evaluate_filter(expr["or"][0], node) or \
                  await self.evaluate_filter(expr["or"][1], node)
        else:
            res = await self.evaluate_filter(expr, node)
        return not res if negated else res

    async def parse_scim_filter(self, node: AST, namespace: str = None) -> Dict:
        if isinstance(node, Filter):
            ns = node.namespace.attr_name if node.namespace else None
            return {
                "negated": node.negated,
                "expr": await self.parse_scim_filter(node.expr, ns or namespace),
            }
        if isinstance(node, AttrExpr):
            # Parse a simple comparison operation:
            operator = node.value.lower()
            attr_path: AttrPath = node.attr_path
            attr = attr_path.attr_name
            if attr_path.sub_attr:
                sub_attr = attr_path.sub_attr.value
                attr = f"{attr}.{sub_attr}"
            comp_value: CompValue = node.comp_value
            parsed = {
                "func": self.filter_map[operator],
                "op": operator,
                "attr": attr,
                "pred": comp_value.value if comp_value else None,
                "namespace": namespace,
            }
            return parsed
        if isinstance(node, LogExpr):
            # Parse a logical expression:
            operator = node.op.lower()
            l_exp = await self.parse_scim_filter(node.expr1, namespace)
            r_exp = await self.parse_scim_filter(node.expr2, namespace)
            return {
                operator: [
                    l_exp,
                    r_exp,
                ]
            }
