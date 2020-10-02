from django.utils import timezone
from scrape.utils import group_datetime

from web.models import Stream, Live


def get_streams(user):
    """
    :param user: User object
    :return: live_list, upc_stream_list, freechat_list
    """
    channel_id_set = user.channel.all().values_list("pk", flat=True)

    # Upcoming Streams
    _stream_list = Stream.objects.filter(channel_id__in=channel_id_set, is_freechat=False, is_removed=False,
                                         start_at__gte=timezone.now()-timezone.timedelta(hours=1)).order_by("start_at")

    upc_stream_list = []
    if _stream_list:
        for t, li in group_datetime(_stream_list):
            upc_stream_list.append((t, li))

    # Free chat List
    freechat_list = Stream.objects.filter(channel_id__in=channel_id_set, is_freechat=True, is_removed=False,
                                          start_at__gte=timezone.now()).order_by("start_at")

    # Streaming Lives
    live_list = Live.objects.filter(is_live=True).order_by("channel_id")

    return live_list, upc_stream_list, freechat_list
