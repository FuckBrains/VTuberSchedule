from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView
from django.utils import timezone
from django.db.models import Q

import requests
import json

from accounts.models import CustomUser
from web.models import Channel, Stream, Live, ServerState
from .forms import UserUpdateForm
from scrape.utils import group_datetime, verify_recaptcha
from web.utils import get_streams


def index(request):
    if not request.user.is_authenticated:
        return render(request, "web/top.html")

    user = get_object_or_404(CustomUser, username=request.user.username)

    live_list, upc_list, freechat_list = get_streams(user)

    return render(request, "web/index.html",
                  {"stream_list": upc_list, "live_list": live_list, "freechat_list": freechat_list})


@login_required
def user_detail(request):
    if request.user.is_authenticated:
        return render(request, "web/user_detail.html", )
    else:
        return redirect("login")


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserUpdateForm
    template_name = "accounts/update.html"
    success_url = reverse_lazy("web:userdetail")

    def get_object(self, queryset=None):
        return self.request.user


def channel_detail(request, channel_id):
    channel = get_object_or_404(Channel, channel_id=channel_id)
    stream_list = channel.stream.filter(channel_id=channel_id).order_by("start_at").reverse()[:50]
    return render(request, "web/channel_detail.html", {"channel": channel, "stream_list": stream_list})


@login_required
def test(request):
    if request.user.is_superuser:
        url = "https://www.youtube.com/channel/%s/videos?view=2&live_view=502" % "UC0TXe_LYZ4scaW2XMyi5_kw"
        cookies = verify_recaptcha(url)
        state, _ = ServerState.objects.update_or_create(key="cookies", value=json.dumps(cookies))

    return redirect("web:index")
