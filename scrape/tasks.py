import logging
import time

from huey import crontab
from huey.contrib.djhuey import periodic_task

from scrape.getStream import get_upcoming_streams, get_streaming_videos
# from django.shortcuts import get_list_or_404
from web.models import Channel

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
    for channel in channel_list:
        func(channel.channel_id)
