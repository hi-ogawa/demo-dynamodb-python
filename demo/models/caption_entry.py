from dataclasses import dataclass

from ..config import schema
from .application import ApplicationBase, auto_id_field


@dataclass
class CaptionEntry(ApplicationBase):
    __schema__ = schema(
        "CaptionEntry",
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "video_id__language", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "CaptionEntry.video_id__language-",
                "KeySchema": [
                    {
                        "AttributeName": "video_id__language",
                        "KeyType": "HASH",
                    },
                ],
                "Projection": {
                    "ProjectionType": "ALL",
                },
            },
        ],
    )
    __extra_attrs__ = ["video_id__language"]

    video_id: str  # Video.id
    language: str
    text: str
    timestamp_start: int  # in second
    timestamp_end: int
    id: str = auto_id_field

    @property
    def video_id__language(self) -> str:
        return "__".join([self.video_id, self.language])
