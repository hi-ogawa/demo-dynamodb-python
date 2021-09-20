from aiohttp.web import Application

from .routes import routes


def create_app() -> Application:
    app = Application()
    app.add_routes(routes)
    return app
