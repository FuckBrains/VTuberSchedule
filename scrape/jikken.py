import json
import os
import re

import django
from pprint import pprint
import time
import chromedriver_binary
import lxml.html
import requests
from jsonpath_ng import parse
from selenium import webdriver

if __name__ == '__main__':
    django.setup()
    from web.models import Channel, Stream, ServerState, Live
    from accounts.models import CustomUser
    from django.utils import timezone
    from scrape.utils import group_datetime
    from huey.contrib.djhuey import HUEY


    # def verify_recaptcha(v_url):
    #     driver = webdriver.Chrome()
    #     driver.get(v_url)
    #
    #     while True:
    #         print(driver.current_url)
    #         if "/sorry/" not in driver.current_url:
    #             c = driver.get_cookies()
    #             break
    #
    #         time.sleep(1)
    #
    #     driver.close()
    #     driver.quit()
    #
    #     _cookies = {}
    #     for cookie in c:
    #         _cookies[cookie["name"]] = cookie["value"]
    #     return _cookies)


    channel_id = "UCSTHImF-20jEFXOPfiyPOhw"

    lives = Live.objects.filter(is_live=True)
    live = lives.first()
    print(live)
    live.is_live = False
    live.save()
    print(live)


def get_streaming_videos(_channel_id):
    """channel_id: Channel id you want to get\n
    save_json: if you want to save the data in json, enter filepath. [optional]\n
    save_html: if you want to save the response as html, enter filepath. [optional]\n"""
    url_base = "https://www.youtube.com/channel/%s/videos?view=2&live_view=501"

    _url = url_base % _channel_id
    try:
        _cookies = json.loads(ServerState.objects.get(key="cookies").value)
    except ServerState.DoesNotExist:
        _cookies = None
    while True:
        _res = requests.get(_url, cookies=_cookies)
        if "/sorry/" in _res.url:
            print(
                "reCaptcha enabled. %s" % _res.url.replace("https://www.google.com/sorry/index?continue=", ""))
            raise ConnectionRefusedError
        _html_src = _res.text
        # print(_res.url)

        if re.search(r"""window\["ytInitialData"\]""", _html_src):
            html = lxml.html.fromstring(_html_src)
            data = json.loads(
                re.search("(.*);", html.xpath("""//body/script[contains(text(), '"ytInitialData"')]""")[
                    0].text.strip().replace("window[\"ytInitialData\"] = ", "")).groups()[0])

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

                if (_live_text == "BADGE_STYLE_TYPE_LIVE_NOW") or (_live_text2 == "LIVE"):
                    title = video.value["title"]["simpleText"]
                    video_id = video.value["videoId"]
                    thumb = 'https://i.ytimg.com/vi/%s/mqdefault.jpg' % video_id

                    videos[video_id] = {"title": title, "thumb": thumb}

            return videos

        time.sleep(5)

