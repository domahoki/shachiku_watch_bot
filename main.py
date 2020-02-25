import sys
import json
import logging
import asyncio
import argparse

import aiohttp
import discord
import responder

from lib.models import init_db
from lib import operations as opers


TWTICH_URL_BASE = "https://www.twitch.tv/{}"
TWITCH_ID_URL = "https://api.twitch.tv/helix/users?login={}"
# HUB_TOPIC_URL = "https://api.twitch.tv/helix/streams?user_id={}"
HUB_TOPIC_URL = "https://api.twitch.tv/helix/users?id={}"
HUB_URL = "https://api.twitch.tv/helix/webhooks/hub"
LEASE_SECONDS = 864000

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


# -- Settings -----------------------------------------------------------------
with open("./settings.json", "r", encoding="utf-8") as fp:
    setting = json.load(fp)

headers = {
    "Content-Type": "application/json",
    "Client-ID": setting["twitch_client_id"]
}

api = responder.API()
client = discord.Client()

# -- Subscriber ---------------------------------------------------------------
@api.route("/webhook/{user_id}")
async def handle_webhooks(req, resp, *, user_id):
    try:
        if req.method == "post":
            # get discord channel by twitch user id
            data = await req.media()
            users = opers.get_users(user_id)
            guilds = [client.get_guild(int(user.guild_id)) for user in users]

            # post on all guilds
            for guild, user in zip(guilds, users):
                channel = opers.get_channel(guild.id)

                if channel is None:
                    logger.error("Faild to get channel.")
                    return

                channel = client.get_channel(int(channel.channel_id))
                if len(data["data"]) == 0:
                    await channel.send(
                        "{}さんの配信が終わったよ.\n{}".format(
                            user.user_name, TWTICH_URL_BASE.format(user.user_name)))

                else:
                    await channel.send(
                        "{}さんの配信が始まったよ.\n{}".format(
                            user.user_name, TWTICH_URL_BASE.format(user.user_name)))

        elif req.method == "get":
            challenge = req.params.get("hub.challenge")
            resp.text = challenge

        else:
            resp.text = "Not implemented method."

    except Exception as ex:
        resp.text = str(ex)

@api.on_event("startup")
async def start_discord_bot():
    client.loop = asyncio.get_running_loop()
    asyncio.create_task(client.start(setting["discord_token"]))

# -- Discord Bot --------------------------------------------------------------

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("/add"):
        await do_subscribe(message)

    if message.content.startswith("/list_users"):
        await get_user_list(message)

    if message.content.startswith("/remove"):
        await do_unsubscribe(message)

    if message.content.startswith("/set_channel"):
        await set_channel(message)

async def do_subscribe(message):
    parsed = message.content.split()
    if len(parsed) != 2:
        await message.channel.send("Format: /add <twitch_username>")
        return

    twitch_name = parsed[-1]
    async with aiohttp.ClientSession() as session:
        async with session.get(
            TWITCH_ID_URL.format(twitch_name),
            headers=headers
        ) as resp:
            json_body = await resp.json()
            if len(json_body["data"]) == 0:
                await message.channel.send("No such user: {}".format(twitch_name))
                return

            user_id = json_body["data"][0]["id"]

    sub_body = {
        "hub.callback": setting["webhook_host"] + user_id,
        "hub.mode": "subscribe",
        "hub.topic": HUB_TOPIC_URL.format(user_id),
        "hub.lease_seconds": LEASE_SECONDS,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            HUB_URL,
            data=json.dumps(sub_body),
            headers=headers
        ) as resp:
            if resp.status == 202:
                result = opers.add_user(
                    user_id=int(user_id),
                    user_name=twitch_name,
                    guild_id=message.channel.guild.id,
                    sub_body=sub_body,
                )

            else:
                result = False

            if result:
                await message.channel.send("Successfully Added!")

            else:
                await message.channel.send(
                    "Add Error With Response: {}".format(resp.status))

async def do_unsubscribe(message):
    parsed = message.content.split()
    if len(parsed) != 2:
        await message.channel.send("Format: /remove <twitch_username>")
        return

    twitch_name = parsed[-1]
    async with aiohttp.ClientSession() as session:
        async with session.get(
            TWITCH_ID_URL.format(twitch_name),
            headers=headers
        ) as resp:
            json_body = await resp.json()
            if len(json_body["data"]) == 0:
                await message.channel.send("No such user: {}".format(twitch_name))
                return

            user_id = json_body["data"][0]["id"]

    sub_info = opers.remove_user(
        user_id=int(user_id),
        guild_id=message.guild.id,
    )
    async with aiohttp.ClientSession() as session:
        async with session.post(
            HUB_URL,
            data=json.dumps(sub_info.get_unsub_body()),
            headers=headers
        ) as resp:
            if resp.status == 202:
                await message.channel.send("Successfully Removed!")

            else:
                await message.channel.send(
                    "Remove Error With Response: {}".format(resp.status))
                return

    return

async def get_user_list(message):
    guild_id = message.guild.id
    users = opers.list_users(guild_id)

    if users is None:
        await message.channel.send("Get user list error.")

    elif len(users) == 0:
        await message.channel.send("No users are registered.")

    else:
        users_str = [str(u) for u in users]
        await message.channel.send("\n".join(users_str))

async def set_channel(message):
    result = opers.register_channel(
        message.guild.id,
        message.channel.id,
    )
    if result is True:
        await message.channel.send("Successfully set channel: {}".format(
            message.channel.name))

    else:
        await message.channel.send("Faild to set channel.")

# -- main ---------------------------------------------------------------------

if __name__ == "__main__":
    parser = parser = argparse.ArgumentParser()
    parser.add_argument("--setting", "-s", type=str, default="settings.json")
    parser.add_argument("--port", "-p", type=int, default=8080)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    args = parser.parse_args()

    # Initialize DB
    init_db()

    with open(args.setting, "r", encoding="utf-8") as fp:
        setting = json.load(fp)

    api.run(address=args.host, port=args.port)
