import json
from bson import ObjectId

from collections import namedtuple
from datetime import datetime, date
from functools import partial
from types import MappingProxyType

import trafaret as t
from aiohttp import web

from .exceptions import JsonValidationError

__all__ = ['json_response', 'jsonify', 'validate_query', 'validate_payload', 'calc_pagination', 'ASC', 'LoginForm', 'MULTI_FIELD_TEXT_QUERY', 'as_dict']


PagingParams = namedtuple('PagingParams', ['limit', 'offset', 'sort_field', 'sort_dir'])
MULTI_FIELD_TEXT_QUERY = 'q'


def json_datetime_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        serial = obj.isoformat()
        return serial

    if ObjectId is not None and isinstance(obj, ObjectId):
        # TODO: try to use bson.json_util instead
        return str(obj)

    raise TypeError("Type not serializable")


jsonify = partial(json.dumps, default=json_datetime_serial)

json_response = partial(web.json_response, dumps=jsonify)


OptKey = partial(t.Key, optional=True)


SimpleType = t.Int | t.Bool | t.String | t.Float
Filter = t.Dict({
    OptKey('in'): t.List(SimpleType),
    OptKey('gt'): SimpleType,
    OptKey('ge'): SimpleType,
    OptKey('lt'): SimpleType,
    OptKey('le'): SimpleType,
    OptKey('ne'): SimpleType,
    OptKey('eq'): SimpleType,
    OptKey('like'): SimpleType,
})


ASC = 'ASC'
DESC = 'DESC'


ListQuery = t.Dict({
    OptKey('_page', default=1): t.Int[1:],
    OptKey('_perPage', default=30): t.Int[1:],
    OptKey('_sortField'): t.String,
    OptKey('_sortDir', default=DESC): t.Enum(DESC, ASC),

    OptKey('_filters'): t.Mapping(t.String, Filter | SimpleType)
})

LoginForm = t.Dict({
    "username": t.String,
    "password": t.String,
})


def validate_query_structure(query):
    """Validate query arguments in list request.

    :param query: mapping with pagination and filtering information
    """
    query_dict = dict(query)
    filters = query_dict.pop('_filters', None)
    if filters:
        try:
            f = json.loads(filters)
        except ValueError:
            msg = '_filters field can not be serialized'
            raise JsonValidationError(msg)
        else:
            query_dict['_filters'] = f
    try:
        q = ListQuery(query_dict)
    except t.DataError as exc:
        msg = '_filters query invalid'
        raise JsonValidationError(msg, **as_dict(exc))

    return q


def validate_payload(raw_payload, schema):
    payload = raw_payload.decode(encoding='UTF-8')
    try:
        parsed = json.loads(payload)
    except ValueError:
        raise JsonValidationError('Payload is not json serialisable')

    try:
        data = schema(parsed)
    except t.DataError as exc:
        raise JsonValidationError(**as_dict(exc))
    return data


def validate_query(query, possible_columns):
    q = validate_query_structure(query)
    sort_field = q.get('_sortField')

    filters = q.get('_filters', [])
    columns = [field_name for field_name in filters]

    if sort_field is not None:
        columns.append(sort_field)

    not_valid = set(columns).difference(
        possible_columns + [MULTI_FIELD_TEXT_QUERY])
    if not_valid:
        column_list = ', '.join(not_valid)
        msg = 'Columns: {} do not present in resource'.format(column_list)
        raise JsonValidationError(msg)
    return MappingProxyType(q)


def calc_pagination(query_dict, default_sort_direction):
    q = query_dict
    page = q['_page']
    sort_field = q.get('_sortField', default_sort_direction)
    per_page = q['_perPage']
    sort_dir = q['_sortDir']
    offset = (page - 1) * per_page
    limit = per_page
    return PagingParams(limit, offset, sort_field, sort_dir)


def as_dict(exc, value=None):
    result = exc.as_dict(value)
    if isinstance(result, str):
        return {"error": result}
    return result
