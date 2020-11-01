from django import forms
from web.models import *


class NoticeForm(forms.Form):
    target_type = forms.ChoiceField(
        choices=(("channel", "Channel"), ("stream", "Stream"))
    )
    action = forms.ChoiceField(
        choices=(("add", "Add"), ("remove", "Remove"))
    )
    target_id = forms.CharField(
        required=True, max_length=24
    )
    notice_min = forms.IntegerField(required=False, max_value=1440, min_value=1)  # Max: 24h, Min: 1m

    def clean_notice_min(self):
        if not self.cleaned_data.get("notice_min"):
            self.cleaned_data["notice_min"] = 5
        return self.cleaned_data.get("notice_min")

    def clean_target_id(self):
        target = self.cleaned_data.get("target_id")
        target_type = self.cleaned_data.get("target_type")
        if target_type == "channel":
            if not Channel.objects.filter(channel_id=target):
                raise forms.ValidationError("Invalid channel/video ID. or target is not registered.")
        elif target_type == "stream":
            if not Stream.objects.filter(video_id=target):
                raise forms.ValidationError("Invalid channel/video ID. or target is not registered.")
        return target

    def clean_action(self):
        action = self.cleaned_data.get("action")
        if action not in ["add", "remove"]:
            raise forms.ValidationError("Invalid parameter - action")
        return action

    def clean_target_type(self):
        if self.cleaned_data.get("target_type") not in ["channel", "stream"]:
            raise forms.ValidationError("Invalid parameter - target_type")
        return self.cleaned_data.get("target_type")
