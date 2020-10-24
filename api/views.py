from django.shortcuts import render, HttpResponse, get_object_or_404
from django.http import HttpResponseBadRequest, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.template.loader import render_to_string

from accounts.models import CustomUser
from web.models import Channel, Stream

from scrape.getChannel import get_subbed_channel
from scrape.getStream import get_upcoming_streams, get_streaming_videos
from web.utils import get_streams

from logging import getLogger

logger = getLogger(__name__)


@require_GET
@login_required
def get_streams(request):
    channel_id = request.GET.get("channelId")

    error, stream_list = get_upcoming_streams(channel_id)
    if error:
        return JsonResponse({"error": error, "code": stream_list[0], "message": stream_list[1]})
    return JsonResponse({"error": False, "data": stream_list})


@require_GET
@login_required
def get_stream_data(request):
    video_id = request.GET.get("videoId")
    try:
        v = Stream.objects.get(video_id=video_id)
    except Stream.DoesNotExist:
        return HttpResponseBadRequest
    return HttpResponse(render_to_string("web/notify_modal_body.html", {"stream": v}))


@require_GET
@login_required
def get_live(request, channel_id):
    error, stream_list = get_streaming_videos(channel_id)
    if error:
        return JsonResponse({"error": error, "code": stream_list[0], "message": stream_list[1]})
    return JsonResponse({"error": False, "data": stream_list})


@require_GET
@login_required
def get_sub_channel(request):
    if request.method != "GET":
        return HttpResponseBadRequest

    user = get_object_or_404(CustomUser, username=request.user.username)
    error, channel_list = get_subbed_channel(user.channel_id)
    if error:
        return JsonResponse({"error": error, "code": channel_list[0], "message": channel_list[1]})
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

    # Process
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

    # Process
    stream = get_object_or_404(Stream, video_id=video_id)
    stream.is_removed = True
    stream.save()
    return JsonResponse({"error": False})


@require_GET
@login_required
def refresh(request):
    user = get_object_or_404(CustomUser, username=request.user.username)
    live_list, upc_list, freechat_list = get_streams(user)

    return HttpResponse(render_to_string("web/main.html", {"live_list": live_list, "stream_list": upc_list,
                                                           "freechat_list": freechat_list, "user": request.user}))
