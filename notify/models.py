from django.db import models

from accounts.models import CustomUser
from web.models import Stream, Channel


class NoticeScheduleStream(models.Model):
    users = models.ManyToManyField(CustomUser, related_name="notice_schedule_streams")
    send_time = models.DateTimeField()
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name="notice_schedule_stream")


class NoticeScheduleChannel(models.Model):
    users = models.ManyToManyField(CustomUser, related_name="notice_schedule_channels")
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="notice_schedule_channel")
