from huey import crontab
from huey.contrib.djhuey import periodic_task
import time

# from django.shortcuts import get_list_or_404
from django.conf import settings
from web.models import Channel

from scrape.getStream import get_upcoming_streams, get_streaming_videos

import logging

logger = logging.getLogger(__name__)


@periodic_task(crontab(minute="*/30"))
def get_stream_each_30_min():
    channel_list = Channel.objects.all()

    start = time.time()
    run_command(get_upcoming_streams, channel_list)
    logger.info("Periodic task completed... [%s] %d s" % ("get_stream_each_30_min()", time.time() - start))


@periodic_task(crontab(minute="*/2"))
def get_live_stream():
    channel_list = Channel.objects.all()

    start = time.time()
    run_command(get_streaming_videos, channel_list)
    logger.info("Periodic task completed... [%s] %d s" % ("get_live_stream()", time.time() - start))


def run_command(func, channel_list):
    workers = settings.HUEY.get("con"
                                "sumer", {}).get("workers", 1)
    for i in range(0, len(channel_list), workers):
        for j, channel in enumerate(channel_list[i:i + workers]):
            r = func(channel.channel_id)
            if j == workers:
                if r(blocking=True) == -1:
                    return
            elif i + j >= len(channel_list) - 1:
                r(blocking=True)
            else:
                r()
