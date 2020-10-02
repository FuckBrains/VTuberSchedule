from django.db import models
from django.contrib.auth.models import AbstractUser

from web.models import Channel


class CustomUser(AbstractUser):
    channel_id = models.CharField(max_length=24, unique=True)
    channel = models.ManyToManyField(Channel, related_name="user")
    nickname = models.CharField(max_length=12)
