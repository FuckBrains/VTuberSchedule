from django.urls import path
from . import views

app_name = "api"
urlpatterns = [
    path("get_stream", views.get_stream_list, name="get_stream"),
    path("notify-modal", views.get_notify_modal, name="get_notify_modal"),
    path("register_subscription", views.register_sub_channel, name="register_subscription"),
    path("set_is_freechat", views.set_is_freechat, name="set_is_freechat"),
    path("remove_stream", views.remove_stream, name="remove_stream"),
    path("refresh", views.refresh, name="refresh"),
    path("notify", views.notify, name="notify"),
    path("youtube_callback", views.youtube_callback, name="youtube_callback")
]
