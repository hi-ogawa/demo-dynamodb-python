import json
import unittest
from os.path import dirname, join
from typing import Any, ClassVar, Type

import boto3

from ..config import config, env
from .application import ApplicationBase
from .caption_entry import CaptionEntry
from .practice_entry import PracticeEntry
from .user import UniqueUsername, User
from .video import Video

model_classes: list[Type[ApplicationBase]] = [
    UniqueUsername,
    User,
    Video,
    CaptionEntry,
    PracticeEntry,
]

player_response_json = join(dirname(__file__), "../../data/ex01.player-response.json")
fr_ttml = join(dirname(__file__), "../../data/ex01.fr.ttml")
en_ttml = join(dirname(__file__), "../../data/ex01.en.ttml")

player_response = json.load(open(player_response_json))


class AllTest(unittest.TestCase):
    client: ClassVar[Any]
    user: ClassVar[User]

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
        for model_class in model_classes:
            model_class.create_table()
        cls.user = User.create("john", "asdfjkl;")

    @classmethod
    def tearDownClass(cls) -> None:
        for model_class in model_classes:
            model_class.delete_table()

    def test_video(self):
        # Create video
        user_id = self.user.id
        youtube_id = player_response["videoDetails"]["videoId"]
        title = player_response["videoDetails"]["title"]
        author = player_response["videoDetails"]["author"]
        language1 = "fr"
        language2 = "en"
        video = Video(user_id, youtube_id, title, author, language1, language2)
        video.put()

        # Create caption entry
        video_id = video.id
        language = "fr"
        text = "vous allez bien. Aujourd'hui, on est le 31 août  2021 et demain on déménage ! Déménager, ça veut  "
        timestamp_start = 6
        timestamp_end = 18
        caption_entry = CaptionEntry(
            video_id, language, text, timestamp_start, timestamp_end
        )
        caption_entry.put()

        # Create practice entry
        caption_entry_id = caption_entry.id
        video_id = video.id
        text = "demain on déménage"
        range_start = 57
        range_end = 75
        language = "fr"
        practice_entry = PracticeEntry(
            caption_entry_id, video_id, language, text, range_start, range_end
        )
        practice_entry.put()
