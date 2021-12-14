# from django.contrib.gis.db.models import PointField

from django.contrib.gis.db.models import PointField
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models

from user.models import UserGroup, User
from utility.cleaners import replace_empty
from utility.models import TimestampModel, TimeSlot


# Create your models here.


class BusinessCategory(TimestampModel):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Business category"
        verbose_name_plural = "Business categories"


class Business(TimestampModel):
    class Status(models.IntegerChoices):
        ACTIVE = 0
        INACTIVE = 1

    name = models.CharField(max_length=40, default=None, blank=False, null=False)
    address = models.CharField(max_length=90, default=None, blank=True, null=True)
    image = ArrayField(models.URLField(max_length=1000), blank=True, null=True)
    group = models.OneToOneField(UserGroup, on_delete=models.CASCADE, null=True, blank=True)
    status = models.IntegerField(choices=Status.choices, default=Status.ACTIVE)
    location = PointField(null=True, blank=True)
    category = models.ForeignKey(BusinessCategory, related_name='businesses', on_delete=models.PROTECT)
    verified = models.BooleanField(default=False, null=False, blank=False)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='created_by')

    def __str__(self):
        return self.name

    def clean(self):
        self.name = replace_empty(self.name)
        self.address = replace_empty(self.address)

    class Meta:
        verbose_name = "Business"
        verbose_name_plural = "Businesses"
        unique_together = (('name', 'created_by'))


class BusinessTimeSlot(TimeSlot):
    business = models.ForeignKey(Business, related_name='timeslots', on_delete=models.CASCADE)

    def clean(self):
        if self.day is None:
            raise ValidationError("Day is required")

    class Meta:
        unique_together = (('business', 'day'))


class ProviderDetail(models.Model):
    provider = models.ForeignKey(User, related_name='provider_detail', on_delete=models.CASCADE, null=True, blank=True)
    business = models.ForeignKey(Business, related_name='provider_business', on_delete=models.CASCADE, null=True,
                                 blank=True)
    about = models.TextField()
    experience = models.TextField()

    def __str__(self):
        return self.provider.username

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['provider', 'business'], name='unique-in-detail')
        ]
