from django.db import models


class PeriodicTask(models.Model):
    name = models.CharField(max_length=32, primary_key=True)
    task_id = models.CharField(max_length=36, unique=True)
    is_running = models.BooleanField()

    def __str__(self):
        return self.task_id
