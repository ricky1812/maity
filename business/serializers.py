from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from business.models import Business, BusinessCategory, BusinessTimeSlot, ProviderDetail

from user.serializers import UserGroupSerializer, UserMaskGroupSerializer, UserSerializer
from utility.serializers import get_timeslot_serializer

from utility.helpers import TimestampField

from datetime import date, datetime
import datetime as dt


class BusinessCategorySerializer(ModelSerializer):
    class Meta:
        model = BusinessCategory
        fields = ['id', 'name']


class BusinessSerializer(ModelSerializer):
    services = SerializerMethodField()
    providers = SerializerMethodField()

    def get_services(self, obj):
        return obj.services.all().count()

    def get_providers(self, obj):
        try:
            if obj.group.users != None:
                return obj.group.users.all().count()
        except:
            return 0

    class Meta:
        model = Business
        fields = ['id', 'name', 'status', 'address', 'services', 'providers', 'image']


class BusinessDetailSerializer(ModelSerializer):
    group = UserGroupSerializer(read_only=True)
    category = BusinessCategorySerializer(read_only=True)
    timeslots = SerializerMethodField()

    def get_timeslots(self, obj):
        all_slots = obj.timeslots
        return BusinessDatesSerializer(all_slots, many=True).data
        # BusinessSlotSerializer = get_timeslot_serializer(model_class=BusinessTimeSlot)
        # return BusinessSlotSerializer(all_slots, many=True).data

    class Meta:
        model = Business
        fields = ['id', 'name', 'image', 'group', 'status', 'category', 'timeslots', 'address', 'location']


class SearchBusinessSerializer(ModelSerializer):
    distance = serializers.IntegerField()
    services = SerializerMethodField()
    providers = SerializerMethodField()

    def get_services(self, obj):
        return obj.services.all().count()

    def get_providers(self, obj):
        try:
            count = obj.group.users.all().count()
        except:
            count = 0

        return count

    class Meta:
        model = Business
        fields = ['id', 'name', 'distance', 'status', 'address', 'services', 'providers', 'image']


class BusinessDatesSerializer(ModelSerializer):
    # timeslots = SerializerMethodField()
    start = SerializerMethodField()
    end = SerializerMethodField()

    def get_start(self, obj):
        start_date = obj.start_date
        start_time = obj.start_time
        start = dt.datetime.combine(start_date, start_time).timestamp() * 1000

        return start

    def get_end(self, obj):
        end_date = obj.end_date
        end_time = obj.end_time
        end = dt.datetime.combine(end_date, end_time).timestamp() * 1000

        return end

    class Meta:
        model = BusinessTimeSlot
        fields = ['id', 'day', 'start_time', 'end_time', 'start', 'end']


class BusinessMaskSerializer(ModelSerializer):
    group = UserMaskGroupSerializer(read_only=True, context={'request': True})
    category = BusinessCategorySerializer(read_only=True)
    timeslots = SerializerMethodField()

    def get_timeslots(self, obj):
        all_slots = obj.timeslots
        return BusinessDatesSerializer(all_slots, many=True).data
        # BusinessSlotSerializer = get_timeslot_serializer(model_class=BusinessTimeSlot)
        # return BusinessSlotSerializer(all_slots, many=True).data

    class Meta:
        model = Business
        fields = ['id', 'name', 'image', 'status', 'group', 'category', 'timeslots', 'address', 'location']


class AverageRatingSerializer(ModelSerializer):
    ratings = SerializerMethodField()

    def get_ratings(self, obj):
        feedbacks = obj.feedback_business.all()
        feedbacks = list(feedbacks)

        count = 0
        sum = 0
        for feedback in feedbacks:
            sum = sum + feedback.ratings
            count = count + 1

        ratings = int(sum / count)

        return ratings

    class Meta:
        model = Business
        fields = ['id', 'name', 'ratings']


class ProviderDetailSerializer(ModelSerializer):
    provider = UserSerializer(read_only=True)

    class Meta:
        model = ProviderDetail
        fields = ['id', 'provider', 'about', 'experience']
