from aiohttp import web

from .admin import (
    AdminHandler,
    setup_admin_handlers,
    setup_admin_on_rest_handlers,
    AdminOnRestHandler,
)
from .consts import PROJ_ROOT, APP_KEY
from .security import Permissions, require, authorize


__all__ = ['AdminHandler', 'setup', 'get_admin', 'Permissions', 'require', 'authorize', '_setup', ]
__version__ = '0.0.2'


def setup(app, resources, name=None, app_key=APP_KEY):
    admin_ = web.Application(loop=app.loop)
    app[app_key] = admin_

    admin_handler = AdminHandler(admin_, resources=resources, name=name, loop=app.loop)

    admin_['admin_handler'] = admin_handler
    setup_admin_handlers(admin_, admin_handler)
    return admin_


def _setup(app, *, schema,  title=None, app_key=APP_KEY, db=None):
    """Initialize the admin-on-rest admin"""

    admin_ = web.Application(loop=app.loop)
    app[app_key] = admin_

    if title:
        schema.title = title

    resources = [
        init(db, info['table'], url=info['url'])
        for init, info in schema.resources
    ]

    admin_handler = AdminOnRestHandler(
        admin_,
        resources=resources,
        loop=app.loop,
        schema=schema,
    )

    admin_['admin_handler'] = admin_handler
    setup_admin_on_rest_handlers(admin_, admin_handler)

    return admin_


def get_admin(app, *, app_key=APP_KEY):
    return app.get(app_key)
