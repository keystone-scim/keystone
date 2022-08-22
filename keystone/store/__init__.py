import re
from abc import ABC
from typing import Dict, List


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

    def clean_up_store(self):
        raise NotImplementedError("Method 'clean_up_store' not implemented")

    async def parse_operation(self, operation: str) -> Dict:
        pattern = re.compile("(\\w+)\\s+(.*)\\s+\"(.*)\"")
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
        s_resource = {**resource}
        for sf in self.sensitive_fields:
            if sf in s_resource:
                del s_resource[sf]
        return s_resource


class DatabaseStore(BaseStore, ABC):
    async def remove_users_from_group(self, user_ids: List[str], group_id: str):
        raise NotImplementedError("Method 'remove_user_from_group' not implemented")

    async def add_user_to_group(self, user_id: str, group_id: str):
        raise NotImplementedError("Method 'add_user_to_group' not implemented")

    async def set_group_members(self, users: List[Dict], group_id: str):
        raise NotImplementedError("Method 'set_group_members' not implemented")


class RDBMSStore(DatabaseStore, ABC):

    async def search_members(self, _filter: str, group_id: str):
        raise NotImplementedError("Method 'search_members' not implemented")


class DocumentStore(DatabaseStore, ABC):
    pass
