from django import forms
from django.core.exceptions import ValidationError

from accounts.models import CustomUser
from scrape.getChannel import get_subbed_channel


class UserUpdateForm(forms.ModelForm):
    nickname = forms.CharField(max_length=12, required=True, widget=forms.TextInput(attrs={"placeholder": "ニックネーム"}))
    channel_id = forms.CharField(max_length=24, required=True,
                                 widget=forms.TextInput(attrs={"placeholder": "チャンネルID"}))

    class Meta:
        model = CustomUser
        fields = ("nickname", "channel_id", "email")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get("instance", None)
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"

    def clean_channel_id(self):
        if self.cleaned_data["channel_id"] != self.user.channel_id:
            error, data = get_subbed_channel(self.cleaned_data["channel_id"])
            if error:
                raise ValidationError("The Channel ID does not found.")
            return self.cleaned_data["channel_id"]

        return self.cleaned_data["channel_id"]
