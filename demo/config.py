import os
from typing import Literal, cast

from pydantic import BaseModel

from .config_utils import load

ENV_PREFIX = "DEMO"

Env = Literal["test", "development", "production"]


def load_env() -> Env:
    _env = os.getenv(f"{ENV_PREFIX}_env", "development")
    assert _env in ["test", "development", "production"]
    return cast(Env, _env)


class Config(BaseModel):
    # boto3.client config
    endpoint_url: str
    region_name: str
    aws_access_key_id: str
    aws_secret_access_key: str

    # namespace for dynamodb table
    table_prefix: str

    jwt_secret: str


env = load_env()
config = load(Config, [f"config/{env}.json"], ENV_PREFIX)


def schema(table_name: str, **kwargs) -> dict:
    return dict(
        TableName=f"{config.table_prefix}-{table_name}",
        BillingMode="PAY_PER_REQUEST",
        **kwargs,
    )
