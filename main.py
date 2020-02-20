import json
import asyncio
import argparse

import aiohttp
import discord
import responder


TWITCH_ID_URL = "https://api.twitch.tv/helix/users?login={}"
HUB_TOPIC_URL = "https://api.twitch.tv/helix/users?id={}"
HUB_URL = "https://api.twitch.tv/helix/webhooks/hub"


# -- Settings -----------------------------------------------------------------
with open("./settings.json", "r", encoding="utf-8") as fp:
    setting = json.load(fp)

headers = {
    "Content-Type": "application/json",
    "Client-ID": setting["twitch_client_id"]
}

api = responder.API()
client = discord.Client()
cur_channel = None

# -- Subscriber ---------------------------------------------------------------
@api.route("/webhook")
async def handle_webhooks(req, resp):
    global cur_channel
    try:
        if req.method == "post":
            data = await req.media()
            await cur_channel.send(str(data))

        elif req.method == "get":
            resp.text = req.params.get("hub.challenge")

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

    if message.content.startswith("/remove"):
        await do_unsubscribe(message)

async def do_subscribe(message):
    global cur_channel
    cur_channel = message.channel
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
            user_id = json_body["data"][0]["id"]

    sub_body = {
        "hub.callback": setting["webhook_host"],
        "hub.mode": "subscribe",
        "hub.topic": HUB_TOPIC_URL.format(user_id),
        "hub.lease_seconds": 60,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            HUB_URL,
            data=json.dumps(sub_body),
            headers=headers
        ) as resp:
            if resp.status == 202:
                await message.channel.send("Successfully Added!")

            else:
                await message.channel.send(
                    "Add Error With Response: {}".format(resp.status_code))

async def do_unsubscribe(message):
    pass

# -- main ---------------------------------------------------------------------

if __name__ == "__main__":
    parser = parser = argparse.ArgumentParser()
    parser.add_argument("--setting", "-s", type=str, default="settings.json")
    args = parser.parse_args()

    with open(args.setting, "r", encoding="utf-8") as fp:
        setting = json.load(fp)

    api.run(address="0.0.0.0", port=8080)
