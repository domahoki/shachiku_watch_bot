import logging
import datetime as dt
from typing import List, Dict

import sqlalchemy

from . import db
from .models import Users, Channels, SubInfo


logger = logging.getLogger(__name__)

def add_user(
    user_id: int,
    user_name: str,
    guild_id: str,
    sub_body: Dict[str, str],
    session:sqlalchemy.orm.session.Session = db.session,
) -> bool:
    """Add a user to DB

    Args:
        user_id (int):
            Twitch UserID.
        user_name (str):
            Twitch Login Name.
        guild_id (str):
            Discord Guild ID.
        sub_body (Dict[str, str]):
            Twitch Webhook Subscription Parameters.
        session (sqlalchemy.orm.session.Session, optional):
            DB Session to operate.
            Default: db.session.
    Returns:
        bool:
            Success or faild.
    """
    try:
        query = session.query(Users).filter(
            Users.user_id == user_id, Users.guild_id == guild_id)
        if query.count() == 0:
            user = Users(
                user_id=user_id,
                user_name=user_name,
                guild_id=guild_id,
                update_date=dt.datetime.now()
            )
            sub_info = SubInfo(
                user_id=user_id,
                callback=sub_body["hub.callback"],
                topic=sub_body["hub.topic"],
                lease_seconds=sub_body["hub.lease_seconds"],
                date=dt.datetime.now()
            )
            session.add(user)
            session.add(sub_info)
            session.commit()

        else:
            user = query.first()
            user.user_name = user_name

            sub_info = session.query(SubInfo).filter(SubInfo.id == user.id).first()
            sub_info.callback = sub_body["hub.callback"]
            sub_info.topic = sub_body["hub.topic"]
            sub_info.lease_seconds = sub_body["hub.lease_seconds"]
            sub_info.date = dt.datetime.now()

            session.commit()

    except Exception as ex:
        logger.exception(ex)
        session.rollback()

        return False

    finally:
        session.close()

    return True

def remove_user(
    user_id: int,
    guild_id: str,
    session: sqlalchemy.orm.session.Session = db.session,
) -> SubInfo:
    """Remove a user from DB

    Args:
        user_id (int):
            Twitch UserID.
        guild_id (str):
            Discord GuildID.
        session (sqlalchemy.orm.session.Session, optional):
            DB session to operate.
            Default: db.session.
    Returns:
        SubInfo:
            Twitch Webhooks SubscriptinInfo.
    """
    try:
        query = session.query(Users).filter(
            Users.user_id == user_id, Users.guild_id == guild_id)
        if query.count() == 0:
            logger.error("No such user registered.")
            return None

        else:
            user = query.first()
            sub_info = session.query(SubInfo).filter(SubInfo.id == user.id).first()
            session.delete(user)
            session.delete(sub_info)

            session.commit()

    except Exception as ex:
        logger.exception(ex)
        return None

    finally:
        session.close()

    return sub_info

def list_users(
    guild_id: str,
    session: sqlalchemy.orm.session.Session = db.session
):
    """List all registered users on guild.

    Args:
        guild_id (str):
            Discord GuildID.
        session (sqlalchemy.orm.session.Session, optional):
            DB session to operate.
            Default: db.session.
    Returns:
        List[Users]:
            registered users list.
    """
    all_users = None
    try:
        all_users = session.query(Users).filter(Users.guild_id == guild_id).all()

    except Exception as ex:
        logger.exception(ex)

    finally:
        session.close()

    return all_users

def get_users(user_id, session=db.session) -> List[Users]:
    users = None
    try:
        query = session.query(Users).filter(Users.user_id == user_id)
        if query.count() == 0:
            logger.error("No such user: {}".format(user_id))

        else:
            users = query.all()

    except Exception as ex:
        logger.exception(ex)

    finally:
        session.close()

    return users

def list_subinfo(session=db.session) -> List[SubInfo]:
    sub_info_list = None
    try:
        sub_info_list = session.query(SubInfo).all()

    except Exception as ex:
        logger.exception(ex)

    finally:
        session.close()

    return sub_info_list

def update_subinfo(sub_info_id: int, session=db.session) -> bool:
    try:
        query = session.query(SubInfo).filter(SubInfo.id == sub_info_id)
        if query.count() == 0:
            logger.error("No such sub-info: {}".format(sub_info_id))
            return False

        else:
            sub_info = query.first()
            sub_info.date = dt.datetime.now()
            session.commit()

    except Exception as ex:
        logger.exception(ex)

        return False

    finally:
        session.close()

    return True

def register_channel(
    guild_id,
    channel_id,
    session=db.session,
):
    try:
        query = session.query(Channels).filter(Channels.guild_id == guild_id)
        if query.count() == 0:
            channel = Channels(
                guild_id=guild_id,
                channel_id=channel_id,
            )
            session.add(channel)

        else:
            channel = query.first()
            channel.guild_id = guild_id
            channel.channel_id = channel_id

        session.commit()

    except Exception as ex:
        logger.exception(ex)
        session.rollback()

        return False

    finally:
        session.close()

    return True

def list_channels(session=db.session):
    all_channels = None
    try:
        all_channels = session.query(Channels).all()

    except Exception as ex:
        logger.exception(ex)

    finally:
        session.close()

    return all_channels

def get_channel(guild_id, session=db.session) -> Channels:
    channel = None
    try:
        query = session.query(Channels).filter(
            Channels.guild_id == guild_id)
        if query.count() == 0:
            logger.error("No such channel: {}".format(guild_id))

            return channel

        channel = query.first()

    except Exception as ex:
        logger.exception(ex)

    finally:
        session.close()

    return channel

def get_channel_by_user(user_id, guild_id, session=db.session) -> str:
    channel_id = None
    try:
        query = session.query(Users).filter(
            Users.user_id == user_id, Users.guild_id == guild_id)
        if query.count() == 0:
            logger.error("No such user: {}".format(user_id))

            return channel_id

        user = query.first()
        query = session.query(Channels).filter(Channels.guild_id == user.guild_id)
        if query.count() == 0:
            logger.error("No valid channel: GuildID={}".format(user.guild_id))

            return channel_id

        channel = query.first()
        channel_id = channel.channel_id

    except Exception as ex:
        logger.exception(ex)

    finally:
        session.close()

    return channel_id
