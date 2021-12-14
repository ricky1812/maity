from django.contrib.gis.db.models import PointField
from django.contrib.postgres.fields import ArrayField

from business.models import Business, BusinessCategory
from business.service.models import Service
from note.models import BasicNoteModel
from user.models import *
from utility.models import TimestampModel


class Task(BasicNoteModel):
    class Status(models.IntegerChoices):
        BUSINESS = 1
        PERSONAL = 0

    status = models.IntegerField(choices=Status.choices, default=Status.PERSONAL)
    business_services = models.ManyToManyField(Service, related_name='tasks')
    start_time = models.DateTimeField(default=None, null=True, blank=True)
    end_time = models.DateTimeField(default=None, null=True, blank=True)
    service_providers = models.ManyToManyField(User, related_name='tasks', blank=True)
    links = ArrayField(models.URLField(max_length=1000), blank=True, null=True)
    location = PointField(null=True, blank=True)

    class Meta:
        ordering = ['start_time']
        unique_together = ("created_by", "title", "created_at")


class SubTasks(TimestampModel):
    start = models.DateTimeField(default=None, blank=True)
    end = models.DateTimeField(default=None, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subtask_provider', null=True)

    def __str__(self):
        return self.task.title


class FeedbackTags(models.Model):
    title = models.CharField(max_length=100, default=None, null=False, blank=False)
    category = models.ForeignKey(BusinessCategory, related_name='feedback_cat', on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Feedback(models.Model):
    provider = models.ForeignKey(User, related_name='feedback_provider', on_delete=models.CASCADE)
    business = models.ForeignKey(Business, related_name='feedback_business', on_delete=models.CASCADE)
    task = models.ForeignKey(Task, related_name='feedback_task', on_delete=models.CASCADE)
    tags = models.ManyToManyField(FeedbackTags, name='feedback_tags', blank=True)
    user = models.ForeignKey(User, related_name='feedback_user', on_delete=models.CASCADE, null=True)
    ratings = models.IntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['provider', 'user', 'task'], name='feedback-in-module')
        ]
