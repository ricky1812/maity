import datetime
from datetime import datetime

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from business.serializers import BusinessSerializer, BusinessCategorySerializer
from note.task.models import Task, SubTasks, Feedback, FeedbackTags
from user.models import User
from user.serializers import UserSerializer, UserGroupSerializer
from utility.helpers import TimestampField


class TaskSerializer(ModelSerializer):
    business = serializers.SerializerMethodField()
    tagged_users = UserSerializer(many=True, read_only=True)
    user_groups = UserGroupSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    start_time = TimestampField()
    end_time = TimestampField()
    service_providers= UserSerializer(many=True, read_only=True)

    def get_business(self, obj):
        if obj.business_services.count():
            business = obj.business_services.first().business
            return BusinessSerializer(business).data
        return None

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'business', 'tagged_users', 'user_groups', 'created_by', 'start_time',
                  'end_time','links','service_providers', 'location','is_archieved', 'hashcode']


class TaskListSerializer(ModelSerializer):
    business = serializers.SerializerMethodField()
    start_time = TimestampField()
    end_time = TimestampField()
    tagged_users = UserSerializer(many=True, read_only=True)
    user_groups = UserGroupSerializer(many=True, read_only=True)

    def get_business(self, obj):
        if obj.business_services.count():
            business = obj.business_services.first().business
            return BusinessSerializer(business).data
        return None

    class Meta:
        model = Task
        fields = ['id', 'title', 'business', 'tagged_users','user_groups','start_time', 'end_time', 'hashcode']


class SubTaskSerializer(ModelSerializer):
    task = serializers.SerializerMethodField()

    def get_task(selfself, obj):
        task = obj.task
        return TaskListSerializer(task).data

    class Meta:
        model = SubTasks
        fields = ['id', 'task', 'start', 'end']


class AppointmentListSerializer(ModelSerializer):
    sub_task = serializers.SerializerMethodField()

    def get_sub_task(self, obj):
        date_id = self.context.get("request")
        date_id = datetime.utcfromtimestamp(float(date_id) / 1000.0).date()

        providers = obj.subtask_provider.all().filter(start__date=date_id)
        return SubTaskSerializer(providers, many=True).data

    class Meta:
        model = User
        fields = ['id', 'username', 'sub_task']


class FeedBackTagSerializer(ModelSerializer):
    category = BusinessCategorySerializer(read_only=True)

    class Meta:
        model = FeedbackTags
        fields = ['id', 'title', 'category']


class FeedBackSerializer(ModelSerializer):
    provider = UserSerializer(read_only=True)
    business = BusinessSerializer(read_only=True)
    task = TaskListSerializer(read_only=True)
    feedback_tags = FeedBackTagSerializer(many=True, read_only=True)

    class Meta:
        model = Feedback
        fields = ['id', 'provider', 'business', 'task', 'feedback_tags', 'ratings']
