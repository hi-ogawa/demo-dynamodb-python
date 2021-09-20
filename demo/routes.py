from aiohttp.web import get, post

from .controller_utils import to_handler
from .controllers.users import UsersController

routes = [
    get("/", to_handler(UsersController, UsersController.create)),
    post("/users/", to_handler(UsersController, UsersController.create)),
]
