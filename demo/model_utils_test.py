import unittest
import uuid
from dataclasses import asdict, dataclass
from typing import Any, ClassVar, Type, TypeVar, cast

import boto3
import pytest
from boto3.dynamodb.conditions import Attr, Key

from .model_utils import Base

TEST_CONFIG = dict(
    endpoint_url="http://localhost:4566",
    region_name="ap-northeast-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

TEST_TABLE_PREFIX = "__model_utils_test__"

T = TypeVar("T", bound="DataclassBase")


class DataclassBase(Base):
    @classmethod
    def to_dict(cls: Type[T], self):
        return asdict(self)

    @classmethod
    def from_dict(cls: Type[T], d: dict) -> T:
        return cast(Any, cls)(**d)


def define_test_model():
    @dataclass
    class Model(DataclassBase):
        __schema__ = {
            "TableName": f"{TEST_TABLE_PREFIX}{uuid.uuid1()}",
            "AttributeDefinitions": [
                {"AttributeName": "username", "AttributeType": "S"},
                {"AttributeName": "password", "AttributeType": "S"},
                {"AttributeName": "age", "AttributeType": "N"},
            ],
            "KeySchema": [
                {"AttributeName": "username", "KeyType": "HASH"},
                {"AttributeName": "age", "KeyType": "RANGE"},
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "User_password",
                    "KeySchema": [
                        {
                            "AttributeName": "password",
                            "KeyType": "HASH",
                        },
                    ],
                    "Projection": {
                        "ProjectionType": "ALL",
                    },
                },
            ],
            "BillingMode": "PAY_PER_REQUEST",
        }
        username: str
        password: str
        age: int = 0

    return Model


class BaseTest(unittest.TestCase):
    client: ClassVar[Any]

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = boto3.client("dynamodb", **TEST_CONFIG)
        Base.__client__ = cls.client

    @classmethod
    def dearDownClass(cls) -> None:
        res = cls.client.list_tables()
        names: list[str] = res["TableNames"]
        for name in names:
            if not name.startswith(TEST_TABLE_PREFIX):
                continue
            cls.client.delete_table(TableName=name)
            cls.client.get_waiter("table_not_exists").wait(TableName=name)

    def test_create_table(self):
        Model = define_test_model()
        Model.create_table()
        assert Model.__schema__["TableName"] in self.client.list_tables()["TableNames"]
        assert Model.__table_description__["TableStatus"] == "ACTIVE"

    def test_delete_table(self):
        Model = define_test_model()
        Model.create_table()
        Model.delete_table()
        assert (
            Model.__schema__["TableName"] not in self.client.list_tables()["TableNames"]
        )

    def test_describe_table(self):
        Model = define_test_model()
        Model.create_table()
        Model.describe_table()
        assert Model.__table_description__["TableStatus"] == "ACTIVE"

    def test_serialize(self):
        Model = define_test_model()
        Model.create_table()
        model = Model("john", "asdfjkl;")
        assert Model.serialize(model) == dict(
            {
                "age": {"N": "0"},
                "password": {"S": "asdfjkl;"},
                "username": {"S": "john"},
            }
        )

    def test_put_and_get(self):
        Model = define_test_model()
        Model.create_table()
        model = Model("john", "asdfjkl;")
        model.put()
        res = Model.get(**model.keys())
        assert model == res

    def test_put_unique_True(self):
        Model = define_test_model()
        Model.create_table()
        Model("barr", "asdf1", 1).put()
        with pytest.raises(self.client.exceptions.ConditionalCheckFailedException):
            Model("barr", "qwer", 1).put()

    def test_put_unique_False(self):
        Model = define_test_model()
        Model.create_table()
        Model("barr", "asdf1", 1).put(unique=False)
        Model("barr", "qwer", 1).put(unique=False)
        res = Model.query(KeyConditionExpression=Key("username").eq("barr"))
        assert len(res) == 1

    def test_update(self):
        Model = define_test_model()
        Model.create_table()
        model = Model("john", "asdfjkl;")
        model.put()
        model.password = "qwertyui"
        model.update()
        res = Model.get(**model.keys())
        assert model == res

    def test_delete(self):
        Model = define_test_model()
        Model.create_table()
        model = Model("john", "asdfjkl;")
        model.put()
        assert model.delete() is True
        res = Model.get(**model.keys())
        assert res is None

    def test_delete_no_exist(self):
        Model = define_test_model()
        Model.create_table()
        model = Model("john", "asdfjkl;")
        assert model.delete() is False

    def test_query_hash(self):
        Model = define_test_model()
        Model.create_table()
        models = [
            Model("barr", "asdf1", 1),
            Model("barr", "asdf2", 2),
            Model("john", "qwer1", 2),
        ]
        for model in models:
            model.put()
        res = Model.query(KeyConditionExpression=Key("username").eq("barr"))
        assert res == models[:2]

    def test_query_hash_and_range(self):
        Model = define_test_model()
        Model.create_table()
        models = [
            Model("barr", "asdf1", 1),
            Model("barr", "asdf2", 2),
            Model("john", "qwer1", 2),
        ]
        for model in models:
            model.put()
        res = Model.query(
            KeyConditionExpression=Key("username").eq("barr") & Key("age").lte(1)
        )
        assert res == models[:1]

    def test_query_gsi(self):
        Model = define_test_model()
        Model.create_table()
        models = [
            Model("barr", "asdf1", 1),
            Model("barr", "qwer", 1),
            Model("john", "qwer", 2),
        ]
        for model in models:
            model.put(unique=False)
        res = Model.query(
            IndexName="User_password", KeyConditionExpression=Key("password").eq("qwer")
        )
        assert res == models[1:]

    def test_scan(self):
        Model = define_test_model()
        Model.create_table()
        # Response is somehow always this order
        models = [
            Model("barr", "asdf1"),
            Model("fooo", "asdf2"),
            Model("john", "qwer1"),
        ]
        for model in models:
            model.put()
        res = Model.scan()
        assert res == models

    def test_scan_filter(self):
        Model = define_test_model()
        Model.create_table()
        models = [
            Model("barr", "asdf1"),
            Model("fooo", "asdf2"),
            Model("john", "qwer1"),
        ]
        for model in models:
            model.put()
        res = Model.scan(FilterExpression=Attr("password").begins_with("asdf"))
        assert res == models[:2]

    def test_scan_raw_filter(self):
        Model = define_test_model()
        Model.create_table()
        models = [
            Model("barr", "asdf1"),
            Model("fooo", "asdf2"),
            Model("john", "qwer1"),
        ]
        for model in models:
            model.put()
        res = Model.scan_raw(
            ScanFilter={
                "password": {
                    "AttributeValueList": [{"S": "asdf"}],
                    "ComparisonOperator": "BEGINS_WITH",
                }
            }
        )
        assert res == models[:2]
