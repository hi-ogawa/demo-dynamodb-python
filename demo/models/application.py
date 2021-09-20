from dataclasses import asdict, field
from datetime import datetime
from typing import Any, Type, TypeVar, cast
from uuid import uuid4

from ..model_utils import Base


def generate_id() -> str:
    return str(uuid4())


def generate_created_at() -> int:
    return int(datetime.utcnow().strftime("%s"))


auto_id_field = field(default_factory=generate_id)

auto_created_at_field = field(default_factory=generate_created_at)

T = TypeVar("T", bound="ApplicationBase")


class ApplicationBase(Base):
    # Extra attributes (in addition to dataclass fields) to persist in dynamodb
    __extra_attrs__: list[str] = []

    @classmethod
    def to_dict(cls: Type[T], self: T) -> dict:
        d = asdict(self)
        for attr in cls.__extra_attrs__:
            d[attr] = getattr(self, attr)
        return d

    @classmethod
    def from_dict(cls: Type[T], d: dict) -> T:
        for attr in cls.__extra_attrs__:
            d.pop(attr, None)
        return cast(Any, cls)(**d)
