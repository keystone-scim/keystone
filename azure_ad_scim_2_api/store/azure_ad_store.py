from typing import Dict, List

import aiohttp

from azure_ad_scim_2_api.store import BaseStore
from azure_ad_scim_2_api.util.config import Config


CONFIG = Config()


class AzureADClient:
    session: aiohttp.ClientSession

    def __init__(self, api_version: str = None, **session_kwargs):
        pass


class AzureADStore(BaseStore):
    resource_db: Dict[str, Dict] = {}
    sensitive_fields = ["password"]

    async def search(self, **kwargs: Dict) -> List[Dict]:
        # TODO: implement
        pass

    async def update(self, resource_id: str, **kwargs: Dict) -> Dict:
        # TODO: implement
        pass

    async def create(self, resource: Dict) -> Dict:
        # TODO: implement
        pass

    async def delete(self, resource_id: str) -> None:
        # TODO: implement
        pass

    async def get_by_id(self, resource_id: str) -> Dict:
        # TODO: implement
        pass

    async def parse_filter(self, expr: str) -> Dict:
        return {}

