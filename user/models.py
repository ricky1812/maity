from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ValidationError
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from note.permissions import OWNER_PERMISSIONS
from utility.cleaners import replace_empty
from utility.models import TimestampModel


class UserGroup(TimestampModel):
    class Classification(models.IntegerChoices):
        PRIVATE = 0
        PUBLIC = 1
        BUSINESS = 2

    image = models.URLField(default=None, blank=True, null=True, max_length=1000)
    name = models.CharField(max_length=32, verbose_name="Group Name")
    description = models.TextField(max_length=250, blank=True, null=False, verbose_name="Group Description")
    classification = models.IntegerField(default=Classification.PRIVATE, choices=Classification.choices)
    last_activity_at = models.DateTimeField(blank=True, null=True)
    group_admin = models.ForeignKey('User', on_delete=models.CASCADE, null=True)

    def clean(self):
        if self.classification == self.Classification.BUSINESS:
            if self.business is None:
                raise ValidationError("Cannot be saved as Business. No Business found")

    def __str__(self):
        return self.name

    class Meta:
        permissions = OWNER_PERMISSIONS
        ordering = ['-last_activity_at']


class User(AbstractUser):
    class Visibility(models.IntegerChoices):
        INVISIBLE = 0
        CONTACTS_ONLY = 1
        ALL = 2

    class Status(models.IntegerChoices):
        ACTIVE = 1
        INACTIVE = 0

    image_url = models.URLField(max_length=1000, blank=True, null=True)
    display_name = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = PhoneNumberField(default=None, unique=True, db_index=True)
    user_groups = models.ManyToManyField(UserGroup, related_name='users', blank=True)
    visibility = models.IntegerField(choices=Visibility.choices, default=Visibility.INVISIBLE)
    status = models.IntegerField(choices=Status.choices, default=Status.INACTIVE)
    blocked_users = models.ManyToManyField('self', related_name='users', blank=True)
    last_login = models.DateTimeField(blank=True, null=True)

    # this field is needed by Guardian auth to work
    groups = models.ManyToManyField(Group, related_name="users", blank=True)

    def __str__(self):
        return self.username

    def clean(self):
        # in admin view empty string is sent to email if not filled
        self.email = replace_empty(self.email)
        self.phone_number = replace_empty(self.phone_number)


def get_anonymous_user_instance(User):
    """Used by django-guardian to make anonymous user"""
    anon_user = {'username': 'Anonymous', 'phone_number': '+911234657890'}
    user = None
    try:
        user = User.objects.get(**anon_user)
    except User.DoesNotExist:
        user = User(**anon_user)
        user.set_password("w{Gmc3DGTqJzkxt")
        user.save()
    return user
