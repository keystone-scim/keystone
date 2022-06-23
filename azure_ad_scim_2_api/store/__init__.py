import re
from typing import Dict


class BaseStore:
    filter_map = {}
    sensitive_fields = ["password"]

    async def get_by_id(self, resource_id: str):
        raise NotImplementedError("Method 'get_by_id' not implemented")

    async def search(self, **kwargs: Dict):
        raise NotImplementedError("Method 'search' not implemented")

    async def update(self, resource_id: str, **kwargs: Dict):
        raise NotImplementedError("Method 'update' not implemented")

    async def create(self, resource: Dict):
        raise NotImplementedError("Method 'create' not implemented")

    async def delete(self, resource_id: str):
        raise NotImplementedError("Method 'delete' not implemented")

    async def parse_filter(self, expr: str):
        raise NotImplementedError("Method 'parse_filter' not implemented")

    async def parse_operation(self, operation: str) -> Dict:
        pattern = re.compile("(\\w+)\\s+(.*)\\s+'(.*)'")
        match = pattern.match(operation)
        try:
            attribute = match.group(1)
            operator = match.group(2).lower()
            predicate = match.group(3)
        except Exception as e:
            raise ValueError("Could not parse operation")
        if operator not in self.filter_map:
            raise ValueError(f"Invalid operator: {operator}")
        return {
            "func": self.filter_map[operator],
            "attr": attribute,
            "pred": predicate,
        }

    async def _sanitize(self, resource: Dict) -> Dict:
        for sf in self.sensitive_fields:
            if sf in resource:
                del resource[sf]
        return resource
