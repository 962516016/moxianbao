from flask import redirect, session, url_for


class LoginMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path != '/' and session.get('username') is None:
            # 未登录且不是根路径，先跳转到当前路由
            return redirect(url_for('/'))

        return self.app(environ, start_response)
