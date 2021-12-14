from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from note.models import Note, ChecklistItem
from note.task.serializers import TaskSerializer, TaskListSerializer

from user.serializers import UserGroupSerializer, UserSerializer


class ChecklistSerializer(ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ['id', 'position', 'name', 'checked']


class NoteSerializer(ModelSerializer):
    checklist = serializers.SerializerMethodField()
    checked_items = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    tagged_users = UserSerializer(many=True, read_only=True)
    user_groups = UserGroupSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    task = TaskListSerializer(read_only=True)

    def get_checklist(self, obj):
        checklist_items = obj.checklist.all().order_by('position')
        return ChecklistSerializer(checklist_items, many=True).data

    class Meta:
        model = Note
        fields = ['id', 'title', 'description', 'task', 'checklist', 'checked_items', 'total_items', 'tagged_users',
                  'user_groups', 'created_by', 'hashcode']

    def get_checked_items(self, obj):
        check = obj.checklist.all().filter(checked=True).count()
        return check

    def get_total_items(self, obj):
        total = obj.checklist.all().count()
        return total


class NoteListSerializer(ModelSerializer):
    tagged_users = UserSerializer(many=True, read_only=True)
    checked_items = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    user_groups = UserGroupSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Note
        fields = ['id', 'title', 'tagged_users', 'user_groups', 'checked_items', 'total_items', 'created_by',
                  'hashcode']

    def get_checked_items(self, obj):
        check = obj.checklist.all().filter(checked=True).count()
        return check

    def get_total_items(self, obj):
        total = obj.checklist.all().count()
        return total
