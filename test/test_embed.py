import os
import sys
import warnings
import logging
import asyncio

import pytest
import discord

src_path = os.path.realpath(__file__)
src_dir = os.path.dirname(src_path)
sys.path.append(os.path.join(src_dir, "../"))

from lib import embed
from lib.setting import Setting

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

setting = Setting.get_instance()
setting.load_setting(os.path.join(src_dir, "../settings.json"))

@pytest.fixture
def loop():
    return asyncio.get_event_loop()

def test_get_game_title(loop):
    failed = loop.run_until_complete(embed.get_game_title("xxxxx"))

    succeed = loop.run_until_complete(embed.get_game_title("32399"))

    assert failed == "Unknown"
    assert succeed == "Counter-Strike: Global Offensive"

def test_get_user_thubmnail(loop):
    succeed = loop.run_until_complete(embed.get_user_thumbnail("domahoki"))
    failed = loop.run_until_complete(embed.get_user_thumbnail(""))

    assert succeed != ""
    assert failed == ""

def test_get_embed(loop):
    received_failed = {
        "data": [],
    }
    received_succeed = {
        "data": [{
            "id": "0123456789",
            "user_id": "5678",
            "user_name": "wjdtkdqhs",
            "game_id": "21779",
            "community_ids": [],
            "type": "live",
            "title": "Best Stream Ever",
            "viewer_count": 417,
            "started_at": "2017-12-01T10:09:45",
            "language": "en",
            "thumbnail_url": "https://link/to/thumbnail.jpg",
        }],
    }
    succeed = loop.run_until_complete(embed.get_embed(
        user_name="testman",
        received_data=received_succeed,
    ))
    failed = loop.run_until_complete(embed.get_embed(
        user_name="testman",
        received_data=received_failed,
    ))

    assert failed == None
    assert isinstance(succeed, discord.Embed)
