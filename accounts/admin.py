from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from . import models


class CustomAdmin(UserAdmin):
    model = models.CustomUser
    fieldsets = UserAdmin.fieldsets
    fieldsets[1][1]["fields"] += ('channel_id',)
    list_display = ['username', 'email', 'channel_id']


admin.site.register(models.CustomUser, CustomAdmin)
