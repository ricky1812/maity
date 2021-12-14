from django.contrib.postgres.fields import ArrayField
from django.db import models


# Custom abstract models
from django.db.models import TimeField, DateField


class TimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class HashModel(models.Model):
    hashcode=models.CharField(max_length=1000, default='0000',unique=True)

    class Meta:
        abstract=True



class TimeSlot(models.Model):
    class Day(models.IntegerChoices):
        MONDAY = 1
        TUESDAY = 2
        WEDNESDAY = 3
        THURSDAY = 4
        FRIDAY = 5
        SATURDAY = 6
        SUNDAY = 7
    day = models.IntegerField(choices=Day.choices, blank=True, null=True)
    start_time = TimeField(blank=True, null=True)
    end_time = TimeField(blank=True, null=True)
    start_date = DateField(blank=True, null=True)
    end_date = DateField(blank=True, null=True)

    class Meta:
        abstract = True
