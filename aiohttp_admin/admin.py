from aiohttp_security import remember, forget
from yarl import URL

from .exceptions import JsonValidationError
from .security import authorize
from .utils import json_response, validate_payload, LoginForm


__all__ = ['AdminHandler', 'setup_admin_handlers', 'setup_admin_on_rest_handlers', 'AdminOnRestHandler']


class AdminHandler:

    def __init__(self, admin, *, resources, name=None, loop):
        self._admin = admin
        self._loop = loop
        self._name = name or 'aiohttp_admin'

        for r in resources:
            r.setup(self._admin, URL('/'))
        self._resources = tuple(resources)

    @property
    def name(self):
        return self._name

    @property
    def resources(self):
        return self._resources

    async def token(self, request):
        raw_payload = await request.read()
        data = validate_payload(raw_payload, LoginForm)
        print('Payload: ', data)
        await authorize(request, data['username'], data['password'])

        payload = {"location": "payload"}
        response = json_response(payload)
        await remember(request, response, data['username'])
        return response

    async def logout(self, request):
        if "Authorization" not in request.headers:
            msg = "Auth header is not present, can not destroy token"
            raise JsonValidationError(msg)
        router = request.app.router
        # location = router["admin.login"].url_for().human_repr()
        location = router["public_timeline"].url_for().human_repr()
        payload = {"location": location}
        response = json_response(payload)
        await forget(request, response)
        return response


def setup_admin_handlers(admin, admin_handler):
    add_route = admin.router.add_route
    a = admin_handler
    add_route('POST', '/token', a.token, name='admin.token')
    add_route('DELETE', '/logout', a.logout, name='admin.logout')


class AdminOnRestHandler:
    def __init__(self, admin, *, resources, loop, schema):
        self._admin = admin
        self._loop = loop
        self.schema = schema

        for r in resources:
            r.setup(self._admin, URL('/'))
        self._resources = tuple(resources)

    @property
    def resources(self):
        return self._resources

    async def token(self, request):
        """
        Validation of user data and generate auth token
        """
        raw_payload = await request.read()
        data = validate_payload(raw_payload, LoginForm)
        await authorize(request, data['username'], data['password'])

        router = request.app.router
        # location = router["admin.index"].url_for().human_repr()
        location = router["timeline"].url_for().human_repr()
        payload = {"location": location}
        response = json_response(payload)
        await remember(request, response, data['username'])

        return response

    async def logout(self, request):
        """
        Simple handler for logout
        """
        if "Authorization" not in request.headers:
            msg = "Auth header is not present, can not destroy token"
            raise JsonValidationError(msg)

        response = json_response()
        await forget(request, response)

        return response


def setup_admin_on_rest_handlers(admin, admin_handler):
    """
    Initialize routes.
    """
    add_route = admin.router.add_route
    a = admin_handler

    add_route('POST', '/token', a.token, name='admin.token')
    add_route('DELETE', '/logout', a.logout, name='admin.logout')
