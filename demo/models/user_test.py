import unittest
from typing import Any, ClassVar

import boto3
import pytest
from pydantic import ValidationError

from ..config import config, env
from .application import ApplicationBase
from .user import UniqueUsername, User


class UserTest(unittest.TestCase):
    client: ClassVar[Any]

    @classmethod
    def setUpClass(cls) -> None:
        assert env == "test"
        cls.client = boto3.client(
            "dynamodb",
            endpoint_url=config.endpoint_url,
            region_name=config.region_name,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
        )
        ApplicationBase.__client__ = cls.client
        User.create_table()
        UniqueUsername.create_table()

    @classmethod
    def tearDownClass(cls) -> None:
        UniqueUsername.delete_table()
        User.delete_table()

    def test_auto_id_field(self):
        user = User("joe", "asdfjkl;")
        assert len(user.id) == 36

    def test_put_user(self):
        user = User("joe", "asdfjkl;")
        user.put()
        user_get = User.get(id=user.id)
        assert user == user_get

    def test_create_unique_username(self):
        User.create("john", "asdfjkl;")
        with pytest.raises(RuntimeError, match='username "john" is already taken'):
            User.create("john", "qwertyui")

    def test_find_by_username(self):
        user1 = User("jonny", "asdfjkl;")
        user1.put()
        user2 = User.find_by_username("jonny")
        user3 = User.find_by_username("ponny")
        assert user2 == user1
        assert user3 == None

    def test_password(self):
        password = "asdfjkl;"
        user = User.init_by_credentials("jimmy", password)
        user.put()
        res = User.find_by_credentials("jimmy", password)
        assert user == res

    def test_username_validation(self):
        username = "@#$%"
        with pytest.raises(ValidationError):
            User.init_by_credentials(username, "asdfjkl;")

    def test_find_by_token_invalid(self):
        invalid_token = "xxxyyyzzz"
        res = User.find_by_token(invalid_token)
        assert res is None

    def test_to_token_and_find_by_token(self):
        user = User.init_by_credentials("jenny", "lastpass")
        user.put()
        token = user.to_token()
        expected = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6Implbm55In0.0SV7Lt3Er1LVt4x4bLMSMI4XnB8sWZ7as7wTqtcu_M8"
        assert token == expected
        res = User.find_by_token(token)
        assert res == user
