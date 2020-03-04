import os
import sys
import datetime as dt
import logging

import pytest
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

src_path = os.path.realpath(__file__)
src_dir = os.path.dirname(src_path)
sys.path.append(os.path.join(src_dir, "../"))

from lib import db
from lib.operations import (
    add_user, remove_user, list_users, get_users,
    list_subinfo, update_subinfo, register_channel,
    list_channels, get_channel, get_channel_by_user,
)
from lib.models import Users, Channels, SubInfo

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


@pytest.fixture
def test_db():
    # OnMemory DB for test
    engine = create_engine("sqlite:///:memory:", echo=False)
    Session = scoped_session(sessionmaker(bind=engine))
    db.Base.metadata.create_all(engine)

    return Session()

def is_matched_user(
    user: Users,
    info: dict,
):
    assert user.user_id == str(info["user_id"])
    assert user.user_name == info["user_name"]
    assert user.guild_id == info["guild_id"]

def is_matched_subinfo(
    sub_info: SubInfo,
    sub_body: dict,
    datetime: dt.datetime = None
):
    assert sub_info.callback == sub_body["hub.callback"]
    assert sub_info.topic == sub_body["hub.topic"]
    assert sub_info.lease_seconds == sub_body["hub.lease_seconds"]

    if datetime is not None:
        assert sub_info.date > datetime

def test_01_add_user(test_db):
    sub_body = {
        "hub.callback": "http://callback/url/",
        "hub.topic": "http://topic/url",
        "hub.lease_seconds": 300,
        "hub.mode": "subscribe"
    }
    sub_body2 = {
        "hub.callback": "http://callback/url/2",
        "hub.topic": "http://topic/url2",
        "hub.lease_seconds": 301,
        "hub.mode": "subscribe"
    }
    user1 = {
        "user_id": 10000,
        "user_name": "testman",
        "guild_id": "hogehogeguild",
    }
    user2 = {
        "user_id": 10001,
        "user_name": "testman",
        "guild_id": "hogehogeguild",
    }
    user3 = {
        "user_id": 10001,
        "user_name": "testman2",
        "guild_id": "hogehogeguild",
    }
    user4 = {
        "user_id": 10000,
        "user_name": "testman",
        "guild_id": "hogehogeguild2",
    }
    now1 = dt.datetime.now()
    add_user(
        **user1,
        sub_body=sub_body,
        session=test_db,
    )
    add_user(
        **user2,
        sub_body=sub_body,
        session=test_db,
    )
    now2 = dt.datetime.now()
    add_user(
        **user3,
        sub_body=sub_body2,
        session=test_db,
    )
    add_user(
        **user4,
        sub_body=sub_body,
        session=test_db,
    )

    user_list1 = list_users(
        guild_id="hogehogeguild",
        session=test_db
    )
    user_list2 = list_users(
        guild_id="hogehogeguild2",
        session=test_db
    )

    assert len(user_list1) == 2
    assert len(user_list2) == 1

    for user in user_list1:
        if user.user_id == "10000":
            is_matched_user(user, user1)

            sub_info = test_db.query(SubInfo).filter(SubInfo.id == user.id).first()
            is_matched_subinfo(sub_info, sub_body, now1)

        elif user.user_id == "10001":
            is_matched_user(user, user3)

            sub_info = test_db.query(SubInfo).filter(SubInfo.id == user.id).first()
            is_matched_subinfo(sub_info, sub_body2, now2)

        else:
            assert False

    for user in user_list2:
        is_matched_user(user, user4)

        sub_info = test_db.query(SubInfo).filter(SubInfo.id == user.id).first()
        is_matched_subinfo(sub_info, sub_body, now2)

def test_remove_user(test_db):
    sub_body = {
        "hub.callback": "http://callback/url/",
        "hub.topic": "http://topic/url",
        "hub.lease_seconds": 300,
        "hub.mode": "subscribe"
    }
    sub_body2 = {
        "hub.callback": "http://callback/url/2",
        "hub.topic": "http://topic/url2",
        "hub.lease_seconds": 301,
        "hub.mode": "subscribe"
    }
    user1 = {
        "user_id": 10000,
        "user_name": "testman",
        "guild_id": "extreameguildid",
    }
    user2 = {
        "user_id": 10001,
        "user_name": "testman2",
        "guild_id": "extreameguildid",
    }
    user3 = {
        "user_id": 10000,
        "user_name": "testman3",
        "guild_id": "extreameguildid2",
    }
    add_user(
        **user1,
        sub_body=sub_body,
        session=test_db,
    )
    add_user(
        **user2,
        sub_body=sub_body2,
        session=test_db,
    )
    add_user(
        **user3,
        sub_body=sub_body2,
        session=test_db,
    )
    remove_user(
        user_id=10000,
        guild_id="extreameguildid",
        session=test_db
    )

    assert test_db.query(Users).count() == 2
    assert test_db.query(SubInfo).count() == 2

    for user in test_db.query(Users).all():
        if user.user_id == "10001":
            is_matched_user(user, user2)

            sub_info = test_db.query(SubInfo).filter(SubInfo.id == user.id).first()
            is_matched_subinfo(sub_info, sub_body2)

        elif user.user_id == "10000":
            is_matched_user(user, user3)

            sub_info = test_db.query(SubInfo).filter(SubInfo.id == user.id).first()
            is_matched_subinfo(sub_info, sub_body2)

        else:
            assert False

def test_03_list_users(test_db):
    user1 = {
        "user_id": 10000,
        "guild_id": "extremeguildid",
        "user_name": "testman",
    }
    user2 = {
        "user_id": 10000,
        "guild_id": "extremeguildid2",
        "user_name": "testman",
    }
    user3 = {
        "user_id": 10001,
        "guild_id": "extremeguildid2",
        "user_name": "testman",
    }
    sub_body = {
        "hub.callback": "http://callback/url/",
        "hub.topic": "http://topic/url",
        "hub.lease_seconds": 300,
        "hub.mode": "subscribe"
    }
    add_user(**user1, sub_body=sub_body, session=test_db)
    add_user(**user2, sub_body=sub_body, session=test_db)
    add_user(**user3, sub_body=sub_body, session=test_db)

    user_list = list_users(guild_id="extremeguildid2", session=test_db)

    assert len(user_list) == 2
    for user in user_list:
        if user.user_id == "10000":
            is_matched_user(user, user2)

        elif user.user_id == "10001":
            is_matched_user(user, user3)

        else:
            assert False

def test_xx_register_channel(test_db):
    register_channel(12345, 12345, session=test_db)
    print(list_channels(session=test_db)[0])

    register_channel(12345, 12343, session=test_db)
    print(list_channels(session=test_db)[0])

    register_channel(12345, 12340, session=test_db)
    print(list_channels(session=test_db)[0])

    register_channel(12345, 12341)
    print(list_channels(session=test_db)[0])
