def setup_routes(app, handler, project_root):
    add_route = app.router.add_route
    add_route('GET', '/', handler.timeline, name='timeline')
    add_route('GET', '/public', handler.public_timeline, name='public_timeline')

    add_route('GET', '/logout', handler.logout, name='logout')
    add_route('POST', '/login', handler.login, name='login')
    add_route('POST', '/register', handler.register, name='register')

    add_route('GET', '/{username}', handler.user_timeline, name='user_timeline')
    add_route('GET', '/{username}/follow', handler.follow_user,  name='follow_user')
    add_route('GET', '/{username}/unfollow', handler.unfollow_user, name='unfollow_user')
    add_route('POST', '/add_message', handler.add_message, name='add_message')
