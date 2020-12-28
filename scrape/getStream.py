import json
import re
import time
from logging import getLogger

import lxml.html
import requests
from dataclasses import dataclass
from django.conf import settings
from django.shortcuts import get_object_or_404
from huey.contrib.djhuey import task
from jsonpath_ng import parse

from web.models import Stream, Channel, Live, ServerState

logger = getLogger(__name__)


@dataclass
class StreamData:
    video_id: str
    channel_id: str
    title: str
    description: str
    start_at: int
    is_freechat: bool


def _get_upcoming_streams_data(_channel_id):
    url_base = "https://www.youtube.com/channel/%s/videos?view=2&live_view=502"

    _url = url_base % _channel_id
    try:
        _cookies = json.loads(ServerState.objects.get(key="cookies").value)
    except ServerState.DoesNotExist:
        _cookies = None

    while True:
        _res = requests.get(_url, cookies=_cookies)
        if "/sorry/" in _res.url:
            logger.warning(
                "reCaptcha enabled. %s" % _res.url.replace("https://www.google.com/sorry/index?continue=", ""))
            raise ConnectionRefusedError
        _html_src = _res.text

        if re.search(r"""window\["ytInitialData"]|var ytInitialData""", _html_src):
            html = lxml.html.fromstring(_html_src)
            json_str = html.xpath("""//body/script[contains(text(), '"ytInitialData"') or
             contains(text(), 'var ytInitialData')]""")[0].text.strip() \
                .replace("window[\"ytInitialData\"] = ", "").replace("var ytInitialData = ", "")
            data = json.loads(re.search("(.*);", json_str).groups()[0])

            videos_json = parse("$..gridVideoRenderer").find(data)
            videos = []
            if not _check_has_upcoming_stream(videos_json):
                return []

            for video in videos_json:
                videos.append(
                    StreamData(
                        video_id=video.value["videoId"],
                        channel_id=_channel_id,
                        title=video.value["title"]["runs"][0]["text"],
                        description=_get_stream_description(video_id=video.value["videoId"]),
                        start_at=int(video.value["upcomingEventData"]["startTime"]),
                        is_freechat=_is_freechat(video.value["title"]["runs"][0]["text"])
                    )
                )

            return videos


def _get_stream_description(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        _cookies = json.loads(ServerState.objects.get(key="cookies").value)
    except ServerState.DoesNotExist:
        _cookies = None
    res = requests.get(url, cookies=_cookies)
    if "/sorry/" in res.url:
        logger.warning(
            "reCaptcha enabled. %s" % res.url.replace("https://www.google.com/sorry/index?continue=", ""))
        raise ConnectionRefusedError

    html_src = res.text
    r = re.search('"description":{"simpleText":"(.+?)"}', html_src)
    if not r:
        logger.error(f"can not find description {video_id}")
        return ""
    return r.group(1)


@task()
def get_upcoming_streams(_channel_id):
    """channel_id: Channel id you want to get\n
    save_json: if you want to save the data in json, enter filepath. [optional]\n
    save_html: if you want to save the response as html, enter filepath. [optional]\n\n
    Return: (bool ERROR, list DATA)\n
        \tif Error is true, Data = (code, message)"""

    api_key = settings.YOUTUBE_API_KEY
    # snippetで叩くと100quota/回 idで叩くと0quota/回 <- id でも 100quotaでした。
    #  liveStreamingDetails->actualStartTime 2quota/time, snippet->title, description, thumbnails 2quota/time
    video_api_url = "https://www.googleapis.com/youtube/v3/videos"

    channel = get_object_or_404(Channel, channel_id=_channel_id)

    # Get upcoming video ids
    video_list = {}
    try:
        # id_list = _get_upcoming_videos_id(_channel_id)
        stream_list = _get_upcoming_streams_data(_channel_id)
    except ConnectionRefusedError:
        return -1
    if not video_list:
        return 0  # Error: False

    for stream_data in stream_list:
        stream, _ = Stream.objects.update_or_create(video_id=stream_data.video_id, defaults={
            "video_id": stream_data.video_id,
            "channel_id": stream_data.channel_id,
            "title": stream_data.title,
            "description": stream_data.description,
            "start_at": stream_data.start_at,
            "is_freechat": stream_data.is_freechat
        })
        if _:
            logger.debug("Added %s %s" % (stream.video_id, stream.title))
        channel.stream.add(stream)

    logger.debug("Done. %s" % channel.channel_id)
    return 0


@task()
def get_streaming_videos(_channel_id):
    # start = time.time()
    # print(f"[GETSTREAM] started. {time.time()-start}")
    # channel = get_object_or_404(Channel, channel_id=_channel_id)

    try:
        video_list = _get_streaming_videos(_channel_id)
    except ConnectionRefusedError:
        return -1

    # print(f"[GETSTREAM] _get_streaming_videos done. {time.time()-start}")
    Live.objects.filter(channel_id=_channel_id, is_live=True).update(is_live=False)
    if not video_list:
        return 0
    # print(f"[GETSTREAM] Live filter done. {time.time()-start}")

    for video_id, data in video_list.items():
        # = {"title": "", "channel_id": _channel_id: "", "thumb": ""}
        data.update({"channel_id": _channel_id, "is_live": True})
        live, _ = Live.objects.update_or_create(video_id=video_id, defaults=data)
        if _:
            logger.debug("Added %s %s" % (live.video_id, live.title))
        else:
            logger.debug("Already added %s %s" % (live.video_id, live.title))

        # channel.live.add(live)
    # print(f"[GETSTREAM] record update done. {time.time()-start}")

    return 0


def _get_streaming_videos(_channel_id):
    """channel_id: Channel id you want to get\n
    save_json: if you want to save the data in json, enter filepath. [optional]\n
    save_html: if you want to save the response as html, enter filepath. [optional]\n"""
    url_base = "https://www.youtube.com/channel/%s/videos?view=2&live_view=501"
    # start = time.time()
    # print(f"[GETSTREAM] _get_streaming_videos started. {time.time()-start}")
    _url = url_base % _channel_id
    try:
        _cookies = json.loads(ServerState.objects.get(key="cookies").value)
    except ServerState.DoesNotExist:
        _cookies = None
    # print(f"[GETSTREAM] cookies loaded. {time.time()-start}")
    while True:
        _res = requests.get(_url, cookies=_cookies)
        if "/sorry/" in _res.url:
            logger.error(
                "reCaptcha enabled. %s" % _res.url.replace("https://www.google.com/sorry/index?continue=", ""))
            raise ConnectionRefusedError
        _html_src = _res.text
        if re.search(r"""window\["ytInitialData"]|var ytInitialData""", _html_src):
            html = lxml.html.fromstring(_html_src)
            json_str = html.xpath("""//body/script[contains(text(), '"ytInitialData"') or
             contains(text(), 'var ytInitialData')]""")[0].text.strip() \
                .replace("window[\"ytInitialData\"] = ", "").replace("var ytInitialData = ", "")
            data = json.loads(re.search("(.*);", json_str).groups()[0])

            videos_json = parse("$..gridVideoRenderer").find(data)

            videos = {}
            for video in videos_json:
                try:
                    _live_text = video.value["badges"][0]["metadataBadgeRenderer"]["style"]
                except KeyError:
                    _live_text = ""
                try:
                    _live_text2 = video.value["thumbnailOverlays"][0]["thumbnailOverlayTimeStatusRenderer"]["style"]
                except KeyError:
                    _live_text2 = ""

                if _live_text == "BADGE_STYLE_TYPE_LIVE_NOW":
                    title = video.value["title"]["simpleText"]
                    video_id = video.value["videoId"]
                    thumb = 'https://i.ytimg.com/vi/%s/mqdefault.jpg' % video_id

                    videos[video_id] = {"title": title, "thumb": thumb}
                elif _live_text2 == "LIVE":
                    title = video.value["title"]["runs"][0]["text"]
                    video_id = video.value["videoId"]
                    thumb = 'https://i.ytimg.com/vi/%s/mqdefault.jpg' % video_id

                    videos[video_id] = {"title": title, "thumb": thumb}

            # print(f"[GETSTREAM] complete. {time.time() - start}")

            return videos

        # print(f"[GETSTREAM] invalid page. {time.time() - start} {_res.url}")
        import os
        if not os.path.exists("invalid.html"):
            with open("invalid.html", "w") as f:
                f.write(_html_src)

        time.sleep(5)


def _check_has_upcoming_stream(video_dict):
    try:
        video_dict[0].value["upcomingEventData"]
    except KeyError:
        return False
    else:
        return True


def _is_freechat(title):
    if re.search(r"(ふり|フリ)[ー～]+?(ちゃっと|チャット)", title):
        return True
    elif re.search(r"[fF]ree.*?[cC]hat", title):
        return True
    else:
        return False
