import re
import uuid
from typing import Dict, List

from azure_ad_scim_2_api.store import BaseStore
from azure_ad_scim_2_api.util.exc import ResourceNotFound, ResourceAlreadyExists


class MemoryStore(BaseStore):
    resource_db: Dict[str, Dict] = {}
    sensitive_fields = ["password"]

    filter_map = {
        "eq": lambda a, b: str(a).lower().__eq__(str(b).lower()),
        "ne": lambda a, b: str(a).lower().__ne__(str(b).lower()),
        "co": lambda a, b: str(a).lower().__contains__(str(b).lower()),
        "sw": lambda a, b: str(a).lower().startswith(str(b).lower()),
        "ew": lambda a, b: str(a).lower().endswith(str(b).lower()),
        "gt": lambda a, b: a > b,
        "ge": lambda a, b: a >= b,
        "lt": lambda a, b: a < b,
        "le": lambda a, b: a <= b,
    }

    async def search(self, **kwargs: Dict) -> List[Dict]:
        pass

    async def _sanitize(self, resource: Dict) -> Dict:
        for sf in self.sensitive_fields:
            if sf in resource:
                del resource[sf]
        return resource

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

    async def parse_filter(self, expr: str) -> Dict:
        return {}

    async def parse_operation(self, operation: str) -> Dict:
        pattern = re.compile("(\w+)\s+(.*)\s+'(.*)'")
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
