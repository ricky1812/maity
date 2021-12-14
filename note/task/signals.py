import channels.layers
from asgiref.sync import async_to_sync
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from note.models import Note, ChecklistItem
from note.serializers import NoteSerializer
from note.task.models import Task
from note.task.serializers import TaskSerializer
from utility.helpers import get_current_time


@receiver(m2m_changed, sender=Task.business_services.through)
def validate_services(sender, instance, **kwargs):
    services = instance.business_services
    if services.count() > 1 and services.values_list('business_id').distinct().count() > 1:
        raise ValidationError("Services from different Businesses selected. Service ids: "
                              + str(services.values_list('id', flat=True)))


@receiver(post_save, sender=Task)
def update_group_active_time(sender, instance, **kwargs):
    user_group = instance.user_groups.all()

    for users in user_group:
        users.last_activity_at = get_current_time()
        users.save()


# .......................................task


# ............................Note

@receiver(m2m_changed, sender=Note.tagged_users.through)
def send_notification(sender, instance, **kwargs):
    all_users = list(instance.tagged_users.all().values_list('id', flat=True))

    action = kwargs.pop('action', None)

    if action == "post_add":

        channel_layer = channels.layers.get_channel_layer()

        for user_id in all_users:
            async_to_sync(channel_layer.group_send)(
                "{}".format(user_id),
                {"type": "tweet_send", "data": NoteSerializer(instance).data, "model": "Note"}
            )


@receiver(m2m_changed, sender=Task.tagged_users.through)
def send_2notification(sender, instance, **kwargs):
    all_users = list(instance.tagged_users.all().values_list('id', flat=True))
    action = kwargs.pop('action', None)

    if action == "post_add":
        channel_layer = channels.layers.get_channel_layer()

        for user_id in all_users:
            async_to_sync(channel_layer.group_send)(
                "{}".format(user_id),
                {"type": "tweet_send", "data": TaskSerializer(instance).data, "model": "Task"}
            )


@receiver(post_save, sender=ChecklistItem)
def send_checklist_notification(sender, instance, **kwargs):
    note = instance.note
    all_users = list(note.tagged_users.all().values_list('id', flat=True))
    # all_users.append(note.created_by.id)

    channel_layer = channels.layers.get_channel_layer()

    for user_id in all_users:
        async_to_sync(channel_layer.group_send)(
            "{}".format(user_id),
            {"type": "tweet_send", "data": NoteSerializer(note).data, "model": "Note"}
        )
