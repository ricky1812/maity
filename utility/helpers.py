import datetime
import pytz
from django.utils import timezone
from rest_framework import serializers
import time


def get_current_time():
    return timezone.now()


class TimestampField(serializers.Field):
    def to_representation(self, value):
        return 1000*value.timestamp()

    def to_internal_value(self, data):
        return datetime.datetime.utcfromtimestamp(float(data) / 1000.0)
