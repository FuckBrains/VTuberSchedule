import collections
import json
import itertools
import time
from selenium import webdriver
import chromedriver_binary

from django.utils import timezone
from web.models import Stream


def save_to_html(_filepath, _data):
    with open(_filepath, "w", encoding="utf-8") as _f:
        _f.write(_data)


def save_to_json(_filepath, _data):
    with open(_filepath, "w", encoding="utf-8") as _f:
        json.dump(_data, _f, ensure_ascii=False, indent=4)


# def split_time(t_list, i, j, k=None):
#     if i > j:
#         if len(t_list) == 1:
#             return Stream.objects.filter(start_at=t_list[0]).values_list("start_at", flat=True)
#         else:
#             return [Stream.objects.filter(start_at=t).values_list("start_at", flat=True) for t in t_list]
#     used = []
#     res = []
#     for t in t_list:
#         if i == 0:
#             a = t.year
#             k = "year"
#         elif i == 1:
#             a = t.month
#             k = "month"
#         elif i == 2:
#             a = t.day
#             k = "day"
#         elif i == 3:
#             a = t.hour
#             k = "hour"
#         elif i == 4:
#             a = t.minute
#             k = "minute"
#         elif i == 5:
#             a = t.second
#             k = "second"
#         elif i == 6:
#             a = t.microsecond
#             k = "microsecond"
#         else:
#             return
#
#         if a in used:
#             res[used.index(a)].append(t)
#         else:
#             res.append([t])
#             used.append(a)
#
#     r = []
#     for li in res:
#         r.append(split_time(li, i + 1, j, k))
#     return r

def group_datetime(stream_list):
    def date_hour(timestamp):
        return timezone.datetime.fromtimestamp(timestamp).strftime("%x %H")

    groups = itertools.groupby(stream_list, lambda x: date_hour(x.start_at.timestamp()))
    # since groups is an iterator and not a list you have not yet traversed the list
    for d, group in groups:
        yield timezone.make_aware(timezone.datetime.strptime(d, "%m/%d/%y %H")), list(group)


def verify_recaptcha(v_url):
    driver = webdriver.Chrome()
    try:
        driver.get(v_url)

        while True:
            if "/sorry/" not in driver.current_url:
                c = driver.get_cookies()
                break

            time.sleep(1)

    except Exception as e:
        driver.close()
        driver.quit()
        raise e
    else:
        driver.close()
        driver.quit()

    _cookies = {}
    for cookie in c:
        _cookies[cookie["name"]] = cookie["value"]
    return _cookies
