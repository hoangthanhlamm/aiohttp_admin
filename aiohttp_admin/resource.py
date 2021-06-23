from abc import abstractmethod, ABCMeta

from bson import ObjectId
from bson.errors import InvalidId

from pymongo import ASCENDING, DESCENDING

from .backends.mongo_utils import create_filter
from .exceptions import ObjectNotFound
from .security import Permissions, require
from .utils import json_response, validate_query, calc_pagination, ASC


class AbstractResource(metaclass=ABCMeta):

    def __init__(self, primary_key, resource_name=None, **kwargs):
        class_name = self.__class__.__name__.lower()
        self._resource_name = resource_name or class_name
        self._primary_key = primary_key

        self.actions = {
            # 'action': ['METHOD', '/{entity_id}'],
            'list': ['GET', ''],
            'detail': ['GET', '/{entity_id}'],
            'create': ['POST', ''],
            'update': ['PUT', '/{entity_id}'],
            'delete': ['DELETE', '/{entity_id}'],
        }

    @property
    def primary_key(self):
        return self._primary_key

    @abstractmethod
    async def list(self, request):  # pragma: no cover
        # await require(request, Permissions.view)
        q = validate_query(request.GET)
        assert q

        # total number of results should be supplied in separate
        headers = {'X-Total-Count': str(0)}
        return json_response({}, headers=headers)

    @abstractmethod
    async def detail(self, request):  # pragma: no cover
        # await require(request, Permissions.view)
        entity_id = request.match_info['entity_id']
        assert entity_id
        return json_response({})

    @abstractmethod
    async def create(self, request):  # pragma: no cover
        # await require(request, Permissions.add)
        return json_response({})

    @abstractmethod
    async def update(self, request):  # pragma: no cover
        # await require(request, Permissions.edit)
        entity_id = request.match_info['entity_id']
        assert entity_id
        return json_response({})

    @abstractmethod
    async def delete(self, request):  # pragma: no cover
        # await require(request, Permissions.delete)
        entity_id = request.match_info['entity_id']
        assert entity_id
        return json_response({})

    def enable(self, action, method='GET', path=''):
        self.actions.update({action: [method, path]})

    def disable(self, action):
        if action in self.actions:
            self.actions.pop(action)

    def setup(self, app, base_url):
        url = str(base_url / self._resource_name)
        add_route = app.router.add_route

        # url_id = url + '/{entity_id}'
        # add_route('GET', url, self.list)
        # add_route('GET', url_id, self.detail)
        # add_route('POST', url, self.create)
        # add_route('PUT', url_id, self.update)
        # add_route('DELETE', url_id, self.delete)

        for action, arg in self.actions.items():
            add_route(arg[0], url + arg[1], self.__getattribute__(action))


class ActionResource:
    def __int__(self, collection, primary_key='_id', **kwargs):
        self._collection = collection
        self._primary_key = primary_key

    async def list_(self, q, schema):
        paging = calc_pagination(q, self._primary_key)
        filters = q.get('_filters')
        query = {}
        if filters:
            query = create_filter(filters, schema)
        projection = [k.name for k in schema.keys]

        sort_direction = ASCENDING if paging.sort_dir == ASC else DESCENDING

        cursor = (self._collection.find(query, projection=projection)
                  .skip(paging.offset)
                  .limit(paging.limit)
                  .sort(paging.sort_field, sort_direction))

        entities = await cursor.to_list(paging.limit)
        count = await self._collection.count_documents(query)
        return entities, count

    async def detail_(self, entity_id):
        try:
            query = {self._primary_key: ObjectId(entity_id)}
        except InvalidId:
            msg = 'Entity with id: {} not found'.format(entity_id)
            raise ObjectNotFound(msg)

        doc = await self._collection.find_one(query)
        if not doc:
            msg = 'Entity with id: {} not found'.format(entity_id)
            raise ObjectNotFound(msg)

        return doc

    async def create_(self, data):
        result = await self._collection.insert_one(data)
        query = {self._primary_key: result.inserted_id}
        doc = await self._collection.find_one(query)
        return doc

    async def update_(self, entity_id, data):
        try:
            query = {self._primary_key: ObjectId(entity_id)}
        except InvalidId:
            msg = 'Entity with id: {} not found'.format(entity_id)
            raise ObjectNotFound(msg)

        doc = await self._collection.find_one_and_update(query, {"$set": data}, upsert=False, new=True)
        if not doc:
            msg = 'Entity with id: {} not found'.format(entity_id)
            raise ObjectNotFound(msg)

        return doc

    async def delete_(self, entity_id):
        try:
            query = {self._primary_key: ObjectId(entity_id)}
        except InvalidId:
            msg = 'Entity with id: {} not found'.format(entity_id)
            raise ObjectNotFound(msg)

        doc = await self._collection.find_one_and_delete(query)
        if not doc:
            msg = 'Entity with id: {} not found'.format(entity_id)
            raise ObjectNotFound(msg)
        return doc
