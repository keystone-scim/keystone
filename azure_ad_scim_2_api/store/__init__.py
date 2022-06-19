from typing import Dict


class BaseStore:

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