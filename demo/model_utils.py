from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Optional, Type, TypeVar, cast

from boto3.dynamodb.transform import ConditionExpressionBuilder
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

# Borrow utilities from boto3
serializer = TypeSerializer()
deserializer = TypeDeserializer()
builder = ConditionExpressionBuilder()


def map_values(d: dict, f: Any) -> dict:
    return {k: f(v) for k, v in d.items()}


def omit(d: dict, keys: list[str]) -> dict:
    return {k: v for k, v in d.items() if k not in keys}


def boto3_serialize(d: dict) -> dict:
    return map_values(d, serializer.serialize)


def boto3_deserialize(d: dict) -> dict:
    return map_values(d, deserializer.deserialize)


def boto3_build_expression(
    KeyConditionExpression=None, FilterExpression=None, **kwargs
) -> dict:
    res = dict(kwargs)
    if KeyConditionExpression is not None:
        exp_string, names, values = builder.build_expression(KeyConditionExpression)
        res.update(
            dict(
                KeyConditionExpression=exp_string,
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=boto3_serialize(values),
            )
        )
    if FilterExpression is not None:
        exp_string, names, values = builder.build_expression(FilterExpression)
        res.update(
            dict(
                FilterExpression=exp_string,
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=boto3_serialize(values),
            )
        )
    return res


# TODO: type-safe
Client = Any
Table = Any

T = TypeVar("T", bound="Base")


class Base(ABC):
    __client__: ClassVar[Client] = None
    __schema__: ClassVar[dict] = {}  # child class must override
    __table_description__: ClassVar[dict] = {}

    @classmethod
    def TableName(cls: Type[T]) -> dict:
        return {"TableName": cls.__schema__["TableName"]}

    @classmethod
    def create_table(cls: Type[T]):
        res = cls.__client__.create_table(**cls.__schema__)
        cls.__table_description__ = res["TableDescription"]
        cls.__client__.get_waiter("table_exists").wait(**cls.TableName())

    @classmethod
    def delete_table(cls: Type[T]):
        cls.__client__.delete_table(**cls.TableName())
        cls.__client__.get_waiter("table_not_exists").wait(**cls.TableName())
        cls.__table_description__ = cast(Any, None)

    @classmethod
    def describe_table(cls: Type[T]):
        res = cls.__client__.describe_table(**cls.TableName())
        cls.__table_description__ = res["Table"]

    @classmethod
    def serialize(cls: Type[T], self: T) -> dict:
        return boto3_serialize(cls.to_dict(self))

    @classmethod
    def deserialize(cls: Type[T], d: dict) -> T:
        return cls.from_dict(boto3_deserialize(d))

    @classmethod
    def key_names(cls: Type[T]) -> list[str]:
        return [attrs["AttributeName"] for attrs in cls.__schema__["KeySchema"]]

    def keys(self: T) -> dict:
        return {name: getattr(self, name) for name in self.key_names()}

    @classmethod
    def unique_keys_condition(cls: Type[T]) -> str:
        return " AND ".join(f"attribute_not_exists({k})" for k in cls.key_names())

    @classmethod
    @abstractmethod
    def to_dict(cls: Type[T], self: T) -> dict:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls: Type[T], d: dict) -> T:
        pass

    #
    # CRUD
    #

    def put_params(self: T, unique=True):
        params = dict(**self.TableName(), Item=self.serialize(self))
        if unique:
            params.update(ConditionExpression=self.unique_keys_condition())
        return params

    def put(self: T, unique=True):
        self.__client__.put_item(**self.put_params(unique=unique))

    @classmethod
    def get(cls: Type[T], **keys: dict) -> Optional[T]:
        res = cls.__client__.get_item(**cls.TableName(), Key=boto3_serialize(keys))
        if item := res.get("Item"):
            return cls.deserialize(item)
        return None

    def update(self: T):
        d = omit(self.serialize(self), self.key_names())
        AttributeUpdates = map_values(d, lambda v: {"Value": v, "Action": "PUT"})
        self.__client__.update_item(
            **self.TableName(),
            Key=boto3_serialize(self.keys()),
            AttributeUpdates=AttributeUpdates,
        )

    def delete(self: T) -> bool:
        res = self.__client__.delete_item(
            **self.TableName(),
            Key=boto3_serialize(self.keys()),
            ReturnValues="ALL_OLD",
        )
        return res.get("Attributes") is not None

    #
    # read many (TODO: Pagination)
    #

    @classmethod
    def query(cls: Type[T], **kwargs) -> list[T]:
        return cls.query_raw(**boto3_build_expression(**kwargs))

    @classmethod
    def scan(cls: Type[T], **kwargs) -> list[T]:
        return cls.scan_raw(**boto3_build_expression(**kwargs))

    @classmethod
    def query_raw(cls: Type[T], **kwargs) -> list[T]:
        res = cls.__client__.query(**cls.TableName(), **kwargs)
        items = res["Items"]
        assert res.get("LastEvaluatedKey") is None  # No pagination needed
        return list(map(cls.deserialize, items))

    @classmethod
    def scan_raw(cls: Type[T], **kwargs) -> list[T]:
        res = cls.__client__.scan(**cls.TableName(), **kwargs)
        items = res["Items"]
        assert res.get("LastEvaluatedKey") is None  # No pagination needed
        return list(map(cls.deserialize, items))

    #
    # TODO: create/destroy many
    #

    @classmethod
    def put_batch(cls):
        assert False

    @classmethod
    def destroy_batch(cls):
        assert False
