from django.contrib import admin
from .models import NoticeScheduleChannel, NoticeScheduleStream

admin.site.register(NoticeScheduleStream)
admin.site.register(NoticeScheduleChannel)
