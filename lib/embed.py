import copy
import asyncio
import aiohttp
import logging
import datetime as dt

import dateutil.parser
from discord import Embed

from .setting import Setting


logger = logging.getLogger(__name__)
GAME_API = "https://api.twitch.tv/helix/games?id={}"
USER_API = "https://api.twitch.tv/helix/users?login={}"
TWTICH_URL_BASE = "https://www.twitch.tv/{}"
TEMPLATE = {
    "title": "",
    "url": "",
    "timestamp": "",
    "image": {
        "url": "",
    },
    "thumbnail": {
        "url": "",
    },
    "author": {
        "name": "",
        "icon_url": "",
    },
    "fields": [
        {
            "name": "Game",
            "value": ""
        }
    ]
}

async def get_game_title(game_id: str) -> str:
    setting = Setting.get_instance()
    async with aiohttp.ClientSession() as session:
        async with session.get(
            GAME_API.format(game_id), headers=setting.get_headers()
        ) as resp:
            json_body = await resp.json()
            if len(json_body["data"]) == 0:
                logger.error("No such game: {}".format(game_id))
                return "Unknown"

            return json_body["data"][0]["name"]

async def get_user_thumbnail(user_name: str) -> str:
    setting = Setting.get_instance()
    async with aiohttp.ClientSession() as session:
        async with session.get(
            USER_API.format(user_name), headers=setting.get_headers()
        ) as resp:
            json_body = await resp.json()
            if json_body.get("error", False):
                logger.error("Unknown user: {}".format(user_name))
                return ""

            return json_body["data"][0]["profile_image_url"]

async def get_message(user_name: str, recieved_data: dict):
    if len(recieved_data["data"]) == 0:
        content = "{}さんの配信が終わったよ.\n{}".format(
            user_name, TWTICH_URL_BASE.format(user_name))
        embed = None

    else:
        content = "{}さんの配信が始まったよ.".format(user_name)
        embed = await get_embed(user_name, recieved_data)

    return content, embed

def parse_iso(iso_str):
    utc = dateutil.parser.parse(iso_str)

    return utc

async def get_embed(user_name: str, received_data: dict):
    if len(received_data["data"]) == 0:
        logger.error("Received Response is Error.")
        return None

    stream_info = received_data["data"][0]
    embed_dict = copy.deepcopy(TEMPLATE)
    user_thumbnail = await get_user_thumbnail(user_name)
    timestamp = parse_iso(stream_info["started_at"])

    embed_dict["title"] = stream_info["title"]
    embed_dict["url"] = TWTICH_URL_BASE.format(user_name)
    embed_dict["timestamp"] = dt.datetime.isoformat(timestamp)
    embed_dict["thumbnail"]["url"] = user_thumbnail
    embed_dict["image"]["url"] = stream_info["thumbnail_url"]
    embed_dict["author"]["name"] = user_name
    embed_dict["author"]["icon_url"] = user_thumbnail
    embed_dict["fields"][0]["value"] = await get_game_title(stream_info["game_id"])

    return Embed.from_dict(embed_dict)
