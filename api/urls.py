from django.urls import path
from . import views

app_name = "api"
urlpatterns = [
    path("get_stream?channelId=<slug:channel_id>", views.get_stream, name="get_stream"),
    path("get_subscription", views.get_sub_channel, name="get_subscription"),
    path("set_is_freechat", views.set_is_freechat, name="set_is_freechat"),
    path("remove_stream", views.remove_stream, name="remove_stream"),
    path("refresh", views.refresh, name="refresh"),
]
