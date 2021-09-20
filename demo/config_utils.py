import json
import os
from typing import Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load(Config: Type[T], filenames: list[str], env_prefix: str) -> T:
    d: dict = {}

    # Load json files
    for filename in filenames:
        with open(filename) as f:
            d.update(json.load(f))

    # Load environment variables
    for key in Config.__fields__.keys():
        if value := os.getenv(f"{env_prefix}_{key}"):
            d[f"{env_prefix}_{key}"] = value

    # Load with pydantic
    return Config.parse_obj(d)
