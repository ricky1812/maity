from django.db.models.signals import post_save
from django.dispatch import receiver

from user.models import UserGroup, User


@receiver(post_save, sender=UserGroup)
@receiver(post_save, sender=User)
def user_post_save(sender, instance, **kwargs):
    """
    Create a Owner corresponding to new User or UserGroup created
    """
    user = None
    user_group = None
    if isinstance(instance, User):
        user = instance
    elif isinstance(instance, UserGroup):
        user_group = instance
    created = kwargs["created"]
#  if created:
#  from note.models import Owner
#  Owner.objects.create(user_group=user_group, user=user)
