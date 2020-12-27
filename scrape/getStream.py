import requests
import re
import json
import lxml.html
from jsonpath_ng import parse
import time

from django.shortcuts import get_object_or_404
from django.conf import settings
from huey.contrib.djhuey import task
from web.models import Stream, Channel, Live, ServerState

from logging import getLogger

logger = getLogger(__name__)


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
        id_list = _get_upcoming_videos_id(_channel_id)
    except ConnectionRefusedError:
        return -1
    if not id_list:
        return 0  # Error: False

    for item in id_list:
        # = {"title": "", "description": "", "channel_id": _channel_id, "thumb": "", "start_at": ""}
        video_list[item] = {"channel_id": _channel_id}

    # Get Start time
    error, items = _get_start_at(video_list, video_api_url, api_key)
    if error:
        return 1

    for item in items:
        video_list[item["id"]]["start_at"] = item["liveStreamingDetails"]["scheduledStartTime"]

    # Get more video details
    error, items = _get_snippet(video_list, video_api_url, api_key)
    if error:
        return 1
    for item in items:
        video_list[item["id"]]["title"] = item["snippet"]["title"]
        if _is_freechat(video_list[item["id"]]["title"]):
            video_list[item["id"]]["is_freechat"] = True
        elif Stream.objects.filter(video_id=[item["id"]]).exists():
            if Stream.objects.get(video_id=[item["id"]])[0].is_freechat:
                video_list[item["id"]]["is_freechat"] = True

        video_list[item["id"]]["description"] = item["snippet"]["description"]
        video_list[item["id"]]["thumb"] = "http://img.youtube.com/vi/%s/mqdefault.jpg" % item["id"]

    for k, v in video_list.items():
        stream, _ = Stream.objects.update_or_create(video_id=k, defaults=v)

        if _:
            logger.debug("Added %s %s" % (stream.video_id, stream.title))

        channel.stream.add(stream)

    logger.debug("Done. %s" % channel.channel_id)
    return 0


@task()
def get_streaming_videos(_channel_id):
    start = time.time()
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


def _get_upcoming_videos_id(_channel_id):
    """channel_id: Channel id you want to get\n
    save_json: if you want to save the data in json, enter filepath. [optional]\n
    save_html: if you want to save the response as html, enter filepath. [optional]\n"""
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

        if re.search(r"""window\["ytInitialData"\]|var ytInitialData""", _html_src):
            html = lxml.html.fromstring(_html_src)
            json_str = html.xpath("""//body/script[contains(text(), '"ytInitialData"') or
             contains(text(), 'var ytInitialData')]""")[0].text.strip() \
                .replace("window[\"ytInitialData\"] = ", "").replace("var ytInitialData = ", "")
            data = json.loads(re.search("(.*);", json_str).groups()[0])

            videos = []
            videos_json = parse("$..gridVideoRenderer").find(data)
            if not _check_has_upcoming_stream(videos_json):
                return []

            for video in videos_json:
                videos.append(video.value["videoId"])

            return videos


def _get_streaming_videos(_channel_id):
    """channel_id: Channel id you want to get\n
    save_json: if you want to save the data in json, enter filepath. [optional]\n
    save_html: if you want to save the response as html, enter filepath. [optional]\n"""
    url_base = "https://www.youtube.com/channel/%s/videos?view=2&live_view=501"
    start = time.time()
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
        # print(_res.url)
        videos = {}
        if re.search(r"""window\["ytInitialData"\]|var ytInitialData""", _html_src):
            html = lxml.html.fromstring(_html_src)
            json_str = html.xpath("""//body/script[contains(text(), '"ytInitialData"') or
             contains(text(), 'var ytInitialData')]""")[0].text.strip() \
                .replace("window[\"ytInitialData\"] = ", "").replace("var ytInitialData = ", "")
            data = json.loads(re.search("(.*);", json_str).groups()[0])

            videos_json = parse("$..gridVideoRenderer").find(data)
            # print(videos_json[0].value)

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


def _get_start_at(_video_list, _video_api_url, _api_key):
    res = requests.get(_video_api_url,
                       params={"part": "liveStreamingDetails", "id": ",".join(list(_video_list.keys())),
                               "maxResults": 50, "key": _api_key})
    live_data = res.json()
    if live_data.get("error"):
        return True, (live_data["error"]["code"], live_data["error"]["message"])
    return False, live_data["items"]


def _get_snippet(_video_list, _video_api_url, _api_key):
    res = requests.get(_video_api_url,
                       params={"part": "snippet", "id": ",".join(list(_video_list.keys())),
                               "maxResults": 50, "key": _api_key})
    snippet_data = res.json()
    if snippet_data.get("error"):
        return True, (snippet_data["error"]["code"], snippet_data["error"]["message"])
    return False, snippet_data["items"]


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


if __name__ == '__main__':
    channel_id = "UCdpUojq0KWZCN9bxXnZwz5w"

    d = _get_streaming_videos(channel_id)
    from pprint import pprint

    pprint(d)
