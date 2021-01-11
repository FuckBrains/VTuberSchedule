import requests

from logging import getLogger

logger = getLogger(__name__)


def get_subbed_channel(access_token):
    api_url = "https://www.googleapis.com/youtube/v3/subscriptions"
    channel_list = []
    next_token = ""
    while True:
        params = {
            "part": "snippet",
            "mine": True,
            "maxResults": 50,
            "access_token": access_token,
            "pageToken": next_token
        }
        res = requests.get(api_url, params)
        if res.status_code != 200:
            return res.text, []
        json = res.json()
        for item in json.get("items"):
            channel_list.append({
                "channel_id": item["snippet"]["channelId"],
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "thumb": item["snippet"]["thumbnails"]["high"]
            })

        if json.get("nextPageToken"):
            next_token = json["nextPageToken"]
        else:
            break

    return False, channel_list


if __name__ == '__main__':
    get_subbed_channel("UCSTHImF-20jEFXOPfiyPOhw")
