from django.test import TestCase, Client
from django.utils import timezone
from accounts.models import CustomUser
from web.models import *
from notify.models import *
from notify.forms import NoticeForm


class NotifyTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(NotifyTest, cls).setUpClass()
        cls.client = Client()
        user = CustomUser.objects.create_user(username="test_user", email="test@test.com", password="1234")
        cls.user = CustomUser.objects.get(username=user.username)
        # cls.user = CustomUser.objects.create(username=user.username, email=user.email, password=user.password)

        cls.channel = Channel.objects.create(channel_id="channelId", description="", title="Channel 1",
                                             thumb="thumb.jpg")
        cls.stream = Stream.objects.create(video_id="videoId", title="Video 1", description="", thumb="thumb.jpg",
                                           start_at=timezone.make_aware(timezone.datetime(2020, 10, 30)),
                                           channel=cls.channel)

    def test_notify_form(self):
        form = NoticeForm(
            data={"target_type": "channel",
                  "action": "add",
                  "target_id": self.channel.channel_id,
                  "notice_min": 5}
        )
        return self.assertTrue(form.is_valid())

    def test_notify_api_channel(self):
        self.client.login(username="test_user", password="1234")

        with self.subTest(msg="Channel test"):
            res = self.client.get("/api/notify", data={
                "target_type": "channel",
                "action": "add",
                "target_id": self.channel.channel_id,
                "notice_min": 5
            })
            print(res.json(), NoticeScheduleChannel.objects.all())
            self.assertTrue(NoticeScheduleChannel.objects.exists())

        with self.subTest(msg="Channel remove"):
            res = self.client.get("/api/notify", data={
                "target_type": "channel",
                "action": "remove",
                "target_id": self.channel.channel_id,
                "notice_min": 5
            })
            print(res.json(), self.user.notice_schedule_channels.all())
            self.assertTrue(not self.user.notice_schedule_channels.exists())

    def test_notify_api_stream(self):
        self.client.login(username="test_user", password="1234")

        with self.subTest(msg="Stream test"):
            res = self.client.get("/api/notify", data={
                "target_type": "stream",
                "action": "add",
                "target_id": self.stream.video_id,
                "notice_min": 5
            })
            print(res.json(), self.user.notice_schedule_streams.all())
            self.assertTrue(self.user.notice_schedule_streams.exists())

        with self.subTest(msg="Stream remove"):
            res = self.client.get("/api/notify", data={
                "target_type": "stream",
                "action": "remove",
                "target_id": self.stream.video_id,
                "notice_min": 5
            })
            print(res.json(), self.user.notice_schedule_streams.all())
            self.assertTrue(not self.user.notice_schedule_streams.exists())
