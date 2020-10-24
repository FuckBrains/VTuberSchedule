from django.urls import path
from . import views

app_name = "api"
urlpatterns = [
    path("get_stream", views.get_streams, name="get_stream"),
    path("stream", views.get_stream_data, name="get_stream_data"),
    path("get_subscription", views.get_sub_channel, name="get_subscription"),
    path("set_is_freechat", views.set_is_freechat, name="set_is_freechat"),
    path("remove_stream", views.remove_stream, name="remove_stream"),
    path("refresh", views.refresh, name="refresh"),
]
