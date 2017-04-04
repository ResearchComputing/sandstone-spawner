import os
import sys
import re
import logging
import tornado.ioloop
from tornado.options import options, define
import tornado.web
import tornado.httpserver
from tornado.web import URLSpec as url

from datetime import date

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(PROJECT_DIR,'client/sandstone')

from sandstone import settings
from sandstone.lib import ui_methods
from sandstone.lib.app_loader import get_installed_app_static_specs
import sandstone.urls
from sandstone.urls import URL_SCHEMA




class SandstoneApplication(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        url_prefix = settings.URL_PREFIX
        app_static_handlers = []
        for spec in get_installed_app_static_specs():
            s_url = r"/static/{}/(.*)".format(spec[0])
            app_static_handlers.append(
                (s_url, tornado.web.StaticFileHandler, {'path': spec[1]})
            )

        # Build the URLSpec for the configured login handler
        login_url = '/auth/login'
        prefixed_login_url = url_prefix + login_url
        login_urlspec = self._build_login_urlspec(login_url)

        handlers = [
                (r"/static/core/(.*)", tornado.web.StaticFileHandler, {'path': STATIC_DIR}),
                login_urlspec,
            ] + app_static_handlers + URL_SCHEMA

        app_settings = dict(
            project_dir=PROJECT_DIR,
            static_dir=STATIC_DIR,
            login_url=prefixed_login_url,
            cookie_secret = settings.COOKIE_SECRET,
            xsrf_cookies=True,
            ui_methods=ui_methods,
            )

        tornado.web.Application.__init__(self, handlers, **app_settings)

        # Apply url prefix to handlers
        self._apply_prefix()
        print self.handlers

    def _apply_prefix(self):
        prefix = settings.URL_PREFIX
        for handler in self.handlers[0][1]:
            handler.regex = re.compile(handler.regex.pattern.replace('/', '{}/'.format(prefix), 1))
            # This is necessary for url reversals to work properly
            handler._path = prefix + handler._path

    def _build_login_urlspec(self, url_path):
        module_path = settings.LOGIN_HANDLER
        module_cmps = module_path.split('.')
        mod_path = '.'.join(module_cmps[:-1])
        handler_class = module_cmps[-1]

        mod = __import__(mod_path, fromlist=[handler_class])
        handler = getattr(mod, handler_class)

        login_urlspec = url(url_path,handler)
        return login_urlspec


def main():
    application = SandstoneApplication(debug=settings.DEBUG)

    define('port', default='8888', help='Port to Run Sandstone application')
    define('token', default='false', help='Use Token auth')
    define('cookie-name')
    define('hub-host')
    define('base-url')
    define('hub-prefix')
    define('hub-api-url')
    define('ip')
    define('user')
    options.parse_command_line()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
