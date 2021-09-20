import base64
import hashlib
from contextlib import suppress
from dataclasses import dataclass
from typing import Optional

import bcrypt
import jwt
from boto3.dynamodb.conditions import Attr
from more_itertools import first
from pydantic import BaseModel, Field, ValidationError

from ..config import config, env, schema
from .application import ApplicationBase, auto_created_at_field, auto_id_field


@dataclass
class User(ApplicationBase):
    __schema__ = schema(
        "User",
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "username", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "User.username-",
                "KeySchema": [
                    {
                        "AttributeName": "username",
                        "KeyType": "HASH",
                    },
                ],
                "Projection": {
                    "ProjectionType": "ALL",
                },
            },
        ],
    )

    username: str
    password_digest: str
    created_at: int = auto_created_at_field
    id: str = auto_id_field

    @classmethod
    def create(self, username: str, password: str) -> "User":
        user = User.init_by_credentials(username, password)
        user.put()
        return user

    def put(self, unique=True):
        assert unique
        if self.find_by_username(self.username) is not None:
            raise RuntimeError(f'username "{self.username}" is already taken')
        unique_username = UniqueUsername(self.username)
        self.__client__.transact_write_items(
            TransactItems=[
                dict(Put=self.put_params()),
                dict(Put=unique_username.put_params()),
            ]
        )

    @classmethod
    def init_by_credentials(cls, username: str, password: str) -> "User":
        CredentialsValidator(
            username=username, password=password
        )  # raises ValidationError
        password_digest = generate_password_digest(password)
        return User(username, password_digest)

    @classmethod
    def find_by_username(cls, username: str) -> Optional["User"]:
        res = cls.query(
            IndexName="User.username-",
            KeyConditionExpression=Attr("username").eq(username),
        )
        return first(res, None)

    @classmethod
    def find_by_credentials(cls, username: str, password: str) -> Optional["User"]:
        user = cls.find_by_username(username)
        if user is not None:
            if verify_passsword(password, user.password_digest):
                return user
        return None

    def to_token(self) -> str:
        return encode_token(self)

    @classmethod
    def find_by_token(cls, token: str) -> Optional["User"]:
        if payload := decode_token(token):
            return cls.find_by_username(payload.username)
        return None


@dataclass
class UniqueUsername(ApplicationBase):
    __schema__ = schema(
        "UniqueUsername",
        AttributeDefinitions=[
            {"AttributeName": "username", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "username", "KeyType": "HASH"},
        ],
    )

    username: str


class CredentialsValidator(BaseModel):
    username: str = Field(regex="^[a-zA-Z0-9_.-]+$")
    password: str


#
# bcrypt password hashing
#

BCRYPT_SALT_ROUNDS = 4 if env == "test" else 12


def generate_password_digest(password: str) -> str:
    password_bin = bytes(password, "utf-8")
    password_bin_sha256 = base64.b64encode(hashlib.sha256(password_bin).digest())
    digest_bin = bcrypt.hashpw(password_bin_sha256, bcrypt.gensalt(BCRYPT_SALT_ROUNDS))
    digest = digest_bin.decode("ascii")
    return digest


def verify_passsword(password: str, digest: str) -> bool:
    password_bin = bytes(password, "utf-8")
    password_bin_sha256 = base64.b64encode(hashlib.sha256(password_bin).digest())
    digest_bin = bytes(digest, "ascii")
    return bcrypt.checkpw(password_bin_sha256, digest_bin)


#
# jwt authentication
#

JWT_ALGORITHM = "HS256"


class TokenPayload(BaseModel):
    username: str


def encode_token(user: User) -> str:
    payload = TokenPayload(username=user.username).dict()
    token = jwt.encode(payload, config.jwt_secret, JWT_ALGORITHM)
    return token


def decode_token(token: str) -> Optional[TokenPayload]:
    with suppress(jwt.exceptions.InvalidTokenError, ValidationError):
        payload = jwt.decode(token, config.jwt_secret, algorithms=[JWT_ALGORITHM])
        return TokenPayload.parse_obj(payload)
    return None
