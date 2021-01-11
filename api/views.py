from django.shortcuts import render, HttpResponse, get_object_or_404
from django.http import HttpResponseBadRequest, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.template.loader import render_to_string

from accounts.models import CustomUser
from web.models import Channel, Stream
from notify.models import NoticeScheduleStream, NoticeScheduleChannel
from notify.forms import NoticeForm

from scrape.getChannel import get_subbed_channel
from scrape.getStream import get_upcoming_streams, get_streaming_videos
from web.utils import get_streams, get_notice_stream_list

import json

from logging import getLogger

logger = getLogger(__name__)


@require_GET
@login_required
def get_stream_list(request):
    channel_id = request.GET.get("channelId")

    error, stream_list = get_upcoming_streams(channel_id)
    if error:
        return JsonResponse({"error": error, "code": stream_list[0], "message": stream_list[1]})
    return JsonResponse({"error": False, "data": stream_list})


@require_GET
@login_required
def get_notify_modal(request):
    video_id = request.GET.get("videoId")
    channel_id = request.GET.get("channelId")
    forms = NoticeForm(data={"notice_min": 5})
    user = CustomUser.objects.get(username=request.user.username)
    # stream_cond_list = user.notice_schedule_streams.all()

    if video_id:
        try:
            v = Stream.objects.get(video_id=video_id)
        except Stream.DoesNotExist:
            return HttpResponseBadRequest
        stream_cond_list = v.notice_schedule_stream.filter(is_active=True)

        return HttpResponse(render_to_string("notify/notify_modal_body.html", {
            "type": "stream",
            "forms": forms,
            "user": user,
            "stream": v,
            "channel": v.channel,
            "active_conditions": stream_cond_list,
            "data": {"is_active_stream": [x.notice_min for x in stream_cond_list],
                     "is_active_channel": [x.notice_min for x in v.channel.notice_schedule_channel.all()]}
        }))
    elif channel_id:
        try:
            c = Channel.objects.get(channel_id=channel_id)
        except Channel.DoesNotExist:
            return HttpResponseBadRequest

        return HttpResponse(render_to_string("notify/notify_modal_body.html", {
            "type": "channel",
            "forms": forms,
            "user": user,
            "channel": c,
            "active_conditions": c.notice_schedule_channel.all(),
            "data": {"is_active_channel": [x.notice_min for x in c.notice_schedule_channel.all()]}
        }))
    else:
        return HttpResponseBadRequest


@require_GET
@login_required
def get_live(request, channel_id):
    error, stream_list = get_streaming_videos(channel_id)
    if error:
        return JsonResponse({"error": error, "code": stream_list[0], "message": stream_list[1]})
    return JsonResponse({"error": False, "data": stream_list})


@require_POST
@login_required
def register_sub_channel(request):
    user = get_object_or_404(CustomUser, username=request.user.username)
    channel_list = json.loads(request.POST.get("channelList"))
    for channel in channel_list:
        c, _ = Channel.objects.update_or_create(channel_id=channel["channel_id"],
                                                defaults={"title": channel["title"], "thumb": channel["thumb"],
                                                          "description": channel["desc"]})
        if _:
            logger.info("Added %s %s" % (c.title, c.channel_id))
        user.channel.add(c)

    logger.debug("%d件の登録チャンネルを取得しました。" % len(channel_list))
    return JsonResponse({"error": False})


@require_GET
@login_required
def set_is_freechat(request):
    if not request.user.is_superuser:
        return JsonResponse({"error": True, "code": "INVALID_REQUEST", "message": "No permission or invalid method"})
    if "v" in request.GET:
        video_id = request.GET["v"]
    else:
        return JsonResponse({"error": True, "code": "NO_V", "message": "No video id in GET params. &v=video_id"})
    if "to" in request.GET:
        set_to = int(request.GET["to"])
        if set_to not in [0, 1]:
            return JsonResponse({"error": True, "code": "NO_TO", "message": "No data to set in GET params. &to=0 or 1"})
    else:
        return JsonResponse({"error": True, "code": "NO_TO", "message": "No data to set in GET params. &to=0 or 1"})

    stream = get_object_or_404(Stream, video_id=video_id)
    if stream.is_freechat == set_to:
        return JsonResponse({"error": True, "code": "INVALID_PARAM", "message": "Current status == param to set."})
    else:
        stream.is_freechat = set_to
        stream.save()

    return JsonResponse({"error": False})


@require_GET
@login_required
def remove_stream(request):
    if not request.user.is_superuser:
        return HttpResponseBadRequest
    if "v" in request.GET:
        video_id = request.GET["v"]
    else:
        return JsonResponse({"error": True, "code": "NO_V", "message": "No video id in GET params. &v=video_id"})

    stream = get_object_or_404(Stream, video_id=video_id)
    stream.is_removed = True
    stream.save()
    return JsonResponse({"error": False})


@require_GET
@login_required
def refresh(request):
    user = get_object_or_404(CustomUser, username=request.user.username)
    live_list, upc_list, freechat_list = get_streams(user)
    notice_list = get_notice_stream_list(user, upc_list)

    return HttpResponse(render_to_string("web/main.html", {"live_list": live_list, "stream_list": upc_list,
                                                           "freechat_list": freechat_list, "user": request.user,
                                                           "notice_list": notice_list}))


@require_GET
@login_required
def notify(request) -> JsonResponse:
    form = NoticeForm(request.GET)
    if not form.is_valid():
        return JsonResponse({"status": False, "errors": form.errors, "msg": "form error"})

    target_type = form.cleaned_data.get("target_type")
    action = form.cleaned_data.get("action")
    target = form.cleaned_data.get("target_id")
    notice_min = form.cleaned_data.get("notice_min")

    if target_type == "channel":
        notice, _ = NoticeScheduleChannel.objects.get_or_create(channel_id=target, notice_min=notice_min)
    elif target_type == "stream":
        notice, _ = NoticeScheduleStream.objects.get_or_create(stream_id=target, notice_min=notice_min)
    else:
        return JsonResponse({"status": False, "errors": ["Invalid target type."]})

    if not notice:
        return JsonResponse({"status": False})

    if action == "add":
        notice.users.add(request.user)
    elif action == "remove":
        notice.users.remove(request.user)
    notice.save()

    return JsonResponse({"status": True})


@require_GET
@login_required
def youtube_callback(request):
    return render(request, "api/youtube_callback.html")
