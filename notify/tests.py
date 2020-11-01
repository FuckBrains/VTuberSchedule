from django.test import TestCase
from unittest import mock
from django.utils import timezone
from web.models import Stream, Channel
from accounts.models import CustomUser
from .views import *
from .models import *
from .tasks import *


class SendMailTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(SendMailTest, cls).setUpClass()
        cls.user = CustomUser.objects.create(username="test_user", email="kadonoboti1@gmail.com", password="1111")
        channel = Channel.objects.create(channel_id="channelId", title="test_channel", thumb="https://www.youtube.jpg")
        stream1 = Stream.objects.create(channel=channel, video_id="videoId1", title="test_video1",
                                        description="Test Video",
                                        start_at=timezone.datetime.strptime("2020/10/30 13", "%Y/%m/%d %H"))
        stream2 = Stream.objects.create(channel=channel, video_id="videoId2", title="test_video2",
                                        description="Test Video",
                                        start_at=timezone.datetime.strptime("2020/10/30 13", "%Y/%m/%d %H"))
        stream3 = Stream.objects.create(channel=channel, video_id="videoId3", title="test_video3",
                                        description="Test Video",
                                        start_at=timezone.datetime.strptime("2020/10/30 13", "%Y/%m/%d %H"))

    def test_send_mail(self):
        result = send_mail(self.user.username, list(Stream.objects.all()))
        self.assertTrue(result)


class NoticeConditionsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(NoticeConditionsTest, cls).setUpClass()
        cls.user = CustomUser.objects.create(username="test_user", email="test@mail.com", password="1234")
        channel = Channel.objects.create(channel_id="channelId", title="test_channel",
                                         thumb="https://www.youtube.jpg")
        channel2 = Channel.objects.create(channel_id="channelId2", title="test_channel",
                                          thumb="https://www.youtube.jpg")
        stream1 = Stream.objects.create(channel=channel, video_id="videoId1", title="test_video1",
                                        description="Test Video",
                                        start_at=timezone.make_aware(timezone.datetime(2020, 10, 30, 19),
                                                                     timezone=timezone.pytz.timezone("Asia/Tokyo")))
        cls.stream1_1 = Stream.objects.create(channel=channel2, video_id="videoId1_1", title="test_video1",
                                          description="Test Video",
                                          start_at=timezone.make_aware(timezone.datetime(2020, 10, 30, 19),
                                                                       timezone=timezone.pytz.timezone("Asia/Tokyo")))
        stream2 = Stream.objects.create(channel=channel, video_id="videoId2", title="test_video2",
                                        description="Test Video",
                                        start_at=timezone.make_aware(timezone.datetime(2020, 10, 30, 10),
                                                                     timezone=timezone.pytz.timezone("Asia/Tokyo")))
        stream3 = Stream.objects.create(channel=channel, video_id="videoId3", title="test_video3",
                                        description="Test Video",
                                        start_at=timezone.make_aware(timezone.datetime(2020, 10, 30, 20),
                                                                     timezone=timezone.pytz.timezone("Asia/Tokyo")))
        nc1 = NoticeScheduleChannel.objects.create(
            channel=channel2, notice_min=5
        )
        nc1.users.add(cls.user)
        ns1 = NoticeScheduleStream.objects.create(
            stream=stream1, notice_min=5
        )
        ns1.users.add(cls.user)

    @mock.patch("notify.views.timezone.now")
    def test_check_cond_channel(self, mocked_now):
        mocked_now.return_value = timezone.make_aware(timezone.datetime(2020, 10, 30, 18, 59))
        r = check_condition_channel()
        return self.assertTrue(NoticeScheduleStream.objects.filter(stream=self.stream1_1).exists())

    @mock.patch("notify.views.timezone.now")
    def test_check_cond_stream(self, mocked_now):
        mocked_now.return_value = timezone.make_aware(timezone.datetime(2020, 10, 30, 18, 59))
        r = check_condition_stream()
        print(r)
        self.assertDictEqual(r, {"test_user": ["videoId1"]})

    @mock.patch("notify.views.timezone.now")
    def test_check_cond(self, mocked_now):
        mocked_now.return_value = timezone.make_aware(timezone.datetime(2020, 10, 30, 18, 59))
        r = check_condition()
        print(r)
        self.assertTrue(True)
