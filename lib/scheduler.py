import json
import logging
import asyncio
import datetime as dt

import aiohttp

from . import operations as opers
from .models import SubInfo
from .setting import Setting


logger = logging.getLogger(__name__)
HUB_URL = "https://api.twitch.tv/helix/webhooks/hub"

async def update_job():
    sub_list = opers.list_subinfo()
    now = dt.datetime.now()
    tasks = list()
    for sub in sub_list:
        expired_date = sub.get_expired_date()
        if now > expired_date:
            task = asyncio.create_task(update_sub(sub))
            tasks.append(task)

    if len(tasks) == 0:
        logger.info("No need to update.")

async def update_sub(sub_info: SubInfo):
    sub_body = sub_info.get_sub_body()
    headers = Setting.get_headers()
    async with aiohttp.ClientSession() as session:
        async with session.post(
            HUB_URL,
            data=json.dumps(sub_body),
            headers=headers
        ) as resp:
            if resp.status == 202:
                result = opers.update_subinfo(sub_info.id)

            else:
                logger.error("Failed to update subscription: {}".format(sub_info))

    if result is True:
        logger.info("Successfully update sub-info: {}".format(sub_info))

    else:
        logger.error("Sub-info update failed: {}".format(sub_info))
