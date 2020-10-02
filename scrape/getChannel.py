import requests

from django.shortcuts import get_object_or_404
from django.conf import settings

from accounts.models import CustomUser
from web.models import Channel

from logging import getLogger

logger = getLogger(__name__)


def get_subbed_channel(_channel_id, save_json=None, save_html=None):
    """channel_id: Channel ID you want to get subscribed channel list\n
    save_json: if you want to save the data in json, enter filepath. [optional]\n
    save_html: if you want to save the response as html, enter filepath. [optional]\n
    """

    api_key = settings.YOUTUBE_API_KEY
    api_url = "https://www.googleapis.com/youtube/v3/subscriptions"

    _url = api_url
    _wrote = False

    _channel_list = []
    page_token = ""

    while True:
        res = requests.get(api_url,
                           params={"part": "snippet", "channelId": _channel_id, "maxResults": 50, "key": api_key,
                                   "pageToken": page_token})
        data = res.json()
        if data.get("error"):
            return True, (data["error"]["code"], data["error"]["message"])
        _channel_list.extend(data["items"])
        if data.get("nextPageToken", None):
            page_token = data.get("nextPageToken", None)
        else:
            break

    r = []
    for channel in _channel_list:
        c_id = channel["snippet"]["resourceId"]["channelId"]
        c_name = channel["snippet"]["title"]
        thumb = channel["snippet"]["thumbnails"]["high"]["url"]
        desc = channel["snippet"]["description"]
        r.append({"channel_id": c_id, "title": c_name, "thumb": thumb, "desc": desc})
        logger.debug("%s %s" % (c_name, c_id))

    user = get_object_or_404(CustomUser, channel_id=_channel_id)
    for channel in r:
        c, _ = Channel.objects.update_or_create(channel_id=channel["channel_id"],
                                                defaults={"title": channel["title"], "thumb": channel["thumb"],
                                                          "description": channel["desc"]})
        if _:
            logger.info("Added %s %s" % (c.title, c.channel_id))
        user.channel.add(c)

    logger.debug("%d件の登録チャンネルを取得しました。 - %s" % (len(r), _channel_id))
    return False, r


if __name__ == '__main__':
    get_subbed_channel("UCSTHImF-20jEFXOPfiyPOhw")
