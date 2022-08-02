import logging
from typing import Dict

from scim_2_api.store import BaseStore
from scim_2_api.util.config import Config

CONFIG = Config()
LOGGER = logging.getLogger(__name__)


class PostgresqlStore(BaseStore):

    async def get_by_id(self, resource_id: str):
        pass

    async def search(self, **kwargs: Dict):
        pass

    async def update(self, resource_id: str, **kwargs: Dict):
        pass

    async def create(self, resource: Dict):
        pass

    async def delete(self, resource_id: str):
        pass

    async def parse_filter_expression(self, expr: str):
        pass

