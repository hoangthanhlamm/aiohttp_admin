from ..resource import AbstractResource, ActionResource
# from ..security import require, Permissions
from ..utils import json_response, validate_payload, validate_query
from .mongo_utils import create_validator


__all__ = ['MotorResource']


class MotorResource(AbstractResource, ActionResource):

    def __init__(self, collection, schema, primary_key='_id', url=None):
        super().__init__(collection=collection, primary_key=primary_key, resource_name=url)
        self._collection = collection
        self._primary_key = primary_key
        self._schema = schema
        self._update_schema = create_validator(schema, primary_key)

    @property
    def primary_key(self):
        return self._primary_key

    async def list(self, request):
        # await require(request, Permissions.view)
        possible_fields = [k.name for k in self._schema.keys]
        q = validate_query(request.query, possible_fields)

        entities, count = await self.list_(q, self._schema)
        headers = {'X-Total-Count': str(count)}
        return json_response(entities, headers=headers)

    async def detail(self, request):
        # await require(request, Permissions.view)
        entity_id = request.match_info['entity_id']

        entity = await self.detail_(entity_id)
        return json_response(entity)

    async def create(self, request):
        # await require(request, Permissions.add)
        raw_payload = await request.read()
        data = validate_payload(raw_payload, self._update_schema)

        doc = await self.create_(data)

        return json_response(doc)

    async def update(self, request):
        # await require(request, Permissions.edit)
        entity_id = request.match_info['entity_id']
        raw_payload = await request.read()
        data = validate_payload(raw_payload, self._update_schema)

        doc = await self.update_(entity_id, data)

        return json_response(doc)

    async def delete(self, request):
        # await require(request, Permissions.delete)
        entity_id = request.match_info['entity_id']

        await self.delete_(entity_id)
        return json_response({'status': 'deleted'})
