from django.db import models


class Stream(models.Model):
    video_id = models.CharField(max_length=11, primary_key=True)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=5500, blank=True)
    thumb = models.CharField(max_length=120)
    channel = models.ForeignKey("Channel", on_delete=models.CASCADE, related_name="stream")
    start_at = models.DateTimeField()
    is_freechat = models.BooleanField(default=False)
    is_removed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["start_at"]


class Live(models.Model):
    video_id = models.CharField(max_length=11, primary_key=True)
    title = models.CharField(max_length=100)
    thumb = models.CharField(max_length=120)
    channel = models.ForeignKey("Channel", on_delete=models.CASCADE, related_name="live")

    is_live = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Channel(models.Model):
    channel_id = models.CharField(max_length=24, primary_key=True)
    title = models.CharField(max_length=50)
    thumb = models.CharField(max_length=120)
    description = models.CharField(max_length=5000, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["title"]


class ServerState(models.Model):
    key = models.CharField(primary_key=True, max_length=32)
    value = models.TextField()

    def __str__(self):
        return self.key
