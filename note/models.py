from django.db import models

from user.models import UserGroup, User
from utility.cleaners import replace_empty
from utility.models import TimestampModel, HashModel


class BasicNoteModel(TimestampModel, HashModel):
    # TODO: Remove owner. A task will always be created by a single user. If the task is for group, group will be
    #  tagged

    user_groups = models.ManyToManyField(UserGroup, name="user_groups", blank=True)
    tagged_users = models.ManyToManyField(User, name='tagged_users', related_name="%(class)s_tagged", blank=True)
    title = models.CharField(max_length=60, blank=False, null=False)
    description = models.CharField(max_length=250, blank=True, null=True)

    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="%(class)s_created", null=False)
    is_archieved = models.BooleanField(default=False)

    def clean(self):
        self.description = replace_empty(self.description, default=None)

    def __str__(self):
        return self.title

    class Meta:
        abstract = True
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['created_by', 'title', 'created_at'], name='unique-in-module')
        ]


class Note(BasicNoteModel):
    from note.task.models import Task
    task = models.ForeignKey(Task, on_delete=models.PROTECT, null=True,blank=True)


class ChecklistItem(TimestampModel, HashModel):
    name = models.CharField(max_length=90, blank=False, null=False)
    checked = models.BooleanField(default=False)
    position = models.PositiveIntegerField()
    note = models.ForeignKey(Note, on_delete=models.CASCADE, null=False, related_name='checklist')

    class Meta:
        unique_together = (('position', 'note'),)

    def __str__(self):
        return self.name
