import os
import sys
import asyncio

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

src_path = os.path.realpath(__file__)
src_dir = os.path.dirname(src_path)
sys.path.append(os.path.join(src_dir, "../"))

from main import handle_webhooks, client
from lib import db
from lib import operations as opers
from lib.setting import Setting


setting = Setting.get_instance()
setting.load_setting(os.path.join(src_dir, "../settings.json"))

class Request(object):
    method = None

    def __init__(self):
        pass

    async def media(self):
        return {
        "data": [{
            "id": "0123456789",
            "user_id": "72151546",
            "user_name": "domahoki",
            "game_id": "21779",
            "community_ids": [],
            "type": "live",
            "title": "Best Stream Ever",
            "viewer_count": 417,
            "started_at": "2017-12-01T10:09:45Z",
            "language": "en",
            "thumbnail_url": "https://theme.zdassets.com/theme_assets/678183/af1a442f9a25a27837f17805b1c0cfa4d1725f90.png",
        }],
    }

class Response(object):
    text = ""

    def __init__(self):
        pass

@pytest.fixture
def test_db():
    # OnMemory DB for test
    engine = create_engine("sqlite:///:memory:", echo=False)
    Session = scoped_session(sessionmaker(bind=engine))
    db.Base.metadata.create_all(engine)

    return Session()

@pytest.fixture
def loop():
    return asyncio.get_event_loop()

def test_handle_webhooks(loop, test_db):
    req = Request()
    req.method = "post"
    resp = Response()

    user_id = "72151546"
    user_name = "domahoki"
    guild_id = "353217051076198410"
    channel_id = "679907365591842846"
    sub_body = {
        "hub.callback": "http://callback/url/",
        "hub.topic": "http://topic/url",
        "hub.lease_seconds": 300,
        "hub.mode": "subscribe"
    }

    opers.register_channel(
        guild_id=guild_id, channel_id=channel_id, session=test_db)
    opers.add_user(
        user_id=user_id, user_name=user_name, guild_id=guild_id,
        sub_body=sub_body, session=test_db)

    async def test_coro(client):
        await client.wait_until_ready()
        result = None

        try:
            await handle_webhooks(
                req, resp, user_id=user_id, session=test_db)

        except Exception as ex:
            result = ex

        finally:
            client.loop.stop()

        return result

    future = asyncio.ensure_future(test_coro(client))
    client.run(setting["discord_token"])

    assert future.result() is None
