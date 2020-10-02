from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = "web"
urlpatterns = [
    path("user", views.user_detail, name="user_detail"),
    path("user/update", login_required(views.UserUpdateView.as_view()), name="user_update"),
    path("channel/<slug:channel_id>", views.channel_detail, name="channel_detail"),
    path("test", views.test, name="test"),
    path("", views.index, name="index"),

]
