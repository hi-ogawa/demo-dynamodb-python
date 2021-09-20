from dataclasses import dataclass

from ..config import schema
from .application import ApplicationBase, auto_created_at_field, auto_id_field


@dataclass
class PracticeEntry(ApplicationBase):
    __schema__ = schema(
        "PracticeEntry",
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {
                "AttributeName": "video_id__language",
                "AttributeType": "S",
            },
            {"AttributeName": "language", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "N"},
        ],
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "PracticeEntry.video_id__language",
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
            {
                "IndexName": "PracticeEntry.language-created_at",
                "KeySchema": [
                    {
                        "AttributeName": "language",
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
    __extra_attrs__ = ["video_id__language"]

    caption_entry_id: str  # CaptionEntry.id
    video_id: str  # Video.id
    language: str
    text: str  # copy of CaptionEntry.text within the selected range
    range_start: int  # offset within CaptionEntry.text
    range_end: int
    created_at: int = auto_created_at_field
    id: str = auto_id_field

    @property
    def video_id__language(self) -> str:
        return "__".join([self.video_id, self.language])
