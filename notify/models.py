from django.db import models

from accounts.models import CustomUser
from web.models import Stream, Channel


class NoticeScheduleStream(models.Model):
    users = models.ManyToManyField(CustomUser, related_name="notice_schedule_streams")
    notice_min = models.IntegerField(default=5)
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name="notice_schedule_stream")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.stream.title

    class Meta:
        unique_together = ["stream", "notice_min"]


class NoticeScheduleChannel(models.Model):
    users = models.ManyToManyField(CustomUser, related_name="notice_schedule_channels")
    notice_min = models.IntegerField(default=5)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="notice_schedule_channel")

    def __str__(self):
        return self.channel.title

    class Meta:
        unique_together = ["channel", "notice_min"]
