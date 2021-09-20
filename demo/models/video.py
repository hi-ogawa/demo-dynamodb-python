from dataclasses import dataclass
from typing import Literal

from ..config import schema
from .application import ApplicationBase, auto_created_at_field, auto_id_field


@dataclass
class Video(ApplicationBase):
    __schema__ = schema(
        "Video",
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "N"},
            {"AttributeName": "is_public", "AttributeType": "N"},
        ],
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "Video.user_id-created_at",
                "KeySchema": [
                    {
                        "AttributeName": "user_id",
                        "KeyType": "HASH",
                    },
                    {
                        "AttributeName": "created_at",
                        "KeyType": "RANGE",
                    },
                ],
                "Projection": {
                    "ProjectionType": "ALL",
                },
            },
            {
                "IndexName": "Video.is_public-created_at",
                "KeySchema": [
                    {
                        "AttributeName": "is_public",
                        "KeyType": "HASH",
                    },
                    {
                        "AttributeName": "created_at",
                        "KeyType": "RANGE",
                    },
                ],
                "Projection": {
                    "ProjectionType": "ALL",
                },
            },
        ],
    )

    user_id: str  # User.id
    youtube_id: str
    title: str
    author: str
    language1: str
    language2: str
    is_public: Literal[0, 1] = 0  # "bool" type cannot be dynamodb HASH, so use "int"
    created_at: int = auto_created_at_field
    id: str = auto_id_field
