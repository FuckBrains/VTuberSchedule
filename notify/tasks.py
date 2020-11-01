from huey.contrib.djhuey import periodic_task, task, db_periodic_task
from huey import crontab
from django.utils import timezone
from .models import NoticeScheduleStream, NoticeScheduleChannel

from .views import check_condition, send_mail, send_web_push
from accounts.models import CustomUser
from logging import getLogger

logger = getLogger(__name__)


@periodic_task(crontab(minute="*/1"))
def notification():
    logger.info("[Notify] Start checking conditions")
    send_list = check_condition()
    for username, video_id_list in send_list.items():
        if video_id_list:
            logger.info(video_id_list)
            print(video_id_list)
            task_send_mail(username, video_id_list)
            task_send_webpush(username, video_id_list)
    return send_list


@task()
def task_send_mail(username, video_id_list):
    user = CustomUser.objects.get(username=username)
    send_mail(user, video_id_list)


@task()
def task_send_webpush(username, video_id_list):
    user = CustomUser.objects.get(username=username)
    for v in video_id_list:
        send_web_push(user, v)


@db_periodic_task(crontab(day="*/7"))
def task_clean_db_notice_stream():
    logger.info("[Clean] Start cleaning NoticeScheduleStream...")
    print("[Clean] Start cleaning NoticeScheduleStream...")
    i = 0
    for item in NoticeScheduleStream.objects.all():
        if item.stream.start_at < timezone.now():
            item.delete()
            i += 1
    logger.info(f"[Clean] Complete cleaning. {i} records deleted")
