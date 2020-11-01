from django.utils import timezone
from django.conf import settings
from sendgrid.helpers.mail import From, Mail, To
import sendgrid
from webpush import send_user_notification

from .models import NoticeScheduleStream, NoticeScheduleChannel
from web.models import Stream, Channel
from accounts.models import CustomUser

from logging import getLogger

logger = getLogger(__name__)


def send_mail(user, video_id_list):
    dist = user.email
    if not dist:
        return
    video_list = [Stream.objects.get(video_id=x) for x in video_id_list]
    tz = timezone.pytz.timezone(user.timezone)

    msg = Mail(
        From(settings.MAIL_ADDR),
        To(dist)
    )
    msg.dynamic_template_data = {
        "video_list": [{
            "video_id": x.video_id, "title": x.title, "thumb_url": x.thumb, "channel_id": x.channel_id,
            "channel_name": x.channel.title, "channel_thumb_url": x.channel.thumb}
            for x in video_list],
        "subject": f"{(video_list[0].start_at - timezone.now()).seconds // 60}分後に生放送が開始されます",
        "start_at": video_list[0].start_at.astimezone(tz).strftime("%m{0}%d{1} %H:%M").format(*"月日"),
        "remain_time_min": (video_list[0].start_at - timezone.now()).total_seconds() // 60,
        # "image": "http://youtube.dplab.biz" + static("images/YoutubeLiveSchedulerHeader.jpg"),
        # "unsubscribe": f"http://giftify.dplab.biz{reverse('account:unsubscribe_page')}?email={dist}&c={_condition_id}"
    }
    msg.template_id = "d-fd0b728c820b424dbe63e4154b47cc4b"
    try:
        sg = sendgrid.SendGridAPIClient(settings.SENDGRID_API)
        response = sg.send(msg.get())
    except Exception as e:
        logger.error(e)
        print(e)
        return None
    logger.debug(f"[NOTIFY] Sent a Mail to {user.email}")
    print(f"[NOTIFY] Sent a Mail to {user.email}")
    return dist


def send_web_push(user, video_id):
    stream = Stream.objects.get(video_id=video_id)
    payload = {
        "head": f"ライブが{int((stream.start_at - timezone.now()).total_seconds()//60)}分後に始まります。",
        "body": stream.title,
        "icon": stream.thumb,
        "url": f"https://www.youtube.com/watch?v={stream.video_id}"
    }
    send_user_notification(user=user, payload=payload, ttl=1000)
    print(f"[NOTIFY] Sent a Webpush to {user.username}")


def check_condition():
    def _combine(a, b):
        for k, v in b.items():
            if k in a.keys():
                a[k] += b[k]
            else:
                a[k] = b[k]
            a[k] = list(set(a[k]))
        return a

    user_dict = _combine(check_condition_channel(), check_condition_stream())
    return user_dict


def check_condition_channel():
    cond_list = NoticeScheduleChannel.objects.all()
    now = timezone.now()

    mailing_list = {}
    for cond in cond_list:
        notice_time = now + timezone.timedelta(minutes=cond.notice_min)
        stream_list = cond.channel.stream.filter(start_at__gte=now, start_at__lte=notice_time)
        if stream_list:
            for stream in stream_list:
                try:
                    ns = NoticeScheduleStream.objects.get(stream=stream)
                except NoticeScheduleStream.DoesNotExist:
                    ns = NoticeScheduleStream.objects.create(
                        stream=stream, notice_min=cond.notice_min
                    )
                    ns.users.add(*cond.users.all())

    return mailing_list


def check_condition_stream():
    cond_list = NoticeScheduleStream.objects.filter(is_active=True)
    now = timezone.now()

    mailing_list = {}
    for cond in cond_list:
        notice_time = now + timezone.timedelta(minutes=cond.notice_min)
        if now <= cond.stream.start_at <= notice_time:
            for user in cond.users.all():
                if user.username in mailing_list.keys():
                    mailing_list[user.username] += cond.stream.video_id
                else:
                    mailing_list[user.username] = [cond.stream.video_id]
                cond.is_active = False
                cond.save()
        if now >= cond.stream.start_at:
            cond.is_active = False
            cond.save()

    return mailing_list
