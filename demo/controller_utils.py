from abc import ABC
from typing import Any, Callable, Coroutine, Type, TypeVar

from aiohttp.web import Request, Response


class BaseController(ABC):
    req: Request

    def __init__(self, req: Request):
        self.req = req

    def process_action(self, action: Callable[[], Coroutine[Any, Any, Response]]):
        return action()


T = TypeVar("T", bound=BaseController)


def to_handler(Controller: Type[T], action: Callable[[T], Coroutine[Any, Any, None]]):
    async def handler(request: Request):
        controller = Controller(request)

        def bound_action():
            return action(controller)

        return controller.process_action(bound_action)

    return handler
