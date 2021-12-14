import datetime
from datetime import datetime, timedelta

from django.db.models import Q
from django.http import HttpResponse
from rest_framework import viewsets, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from business.models import Business
from business.service.models import Service
from note.models import Note, ChecklistItem
from note.paginators import NoteListPaginator
from note.serializers import NoteSerializer, NoteListSerializer, ChecklistSerializer
from note.task.models import Task
from note.task.serializers import TaskListSerializer
from user.models import User, UserGroup
from user.permissions import IsGroupAdmin
from user.serializers import UserSerializer, UserGroupSerializer, UserMaskGroupSerializer
from .permissions import IsListCreator, IsCreator, IsCheckListCreator, IsInCheckList
from rest_framework.exceptions import PermissionDenied
from phonenumber_field.modelfields import PhoneNumberField

from rest_framework.response import Response


def get_note_queryset(user: User):
    user = user
    groups = user.user_groups.all()

    return Note.objects.filter(Q(user_groups__in=groups) | Q(created_by=user) | Q(tagged_users=user)).distinct()


def get_task_queryset(user: User):
    ''' returns all tasks for which user is part of. '''
    user = user
    groups = user.user_groups.all()
    business_groups = UserGroup.objects.all().filter(classification=2).filter(group_admin=user)
    business = Business.objects.filter(group__in=business_groups)
    services = Service.objects.all().filter(business__in=business)
    queryset = Task.objects.filter(
        Q(user_groups__in=groups) | Q(created_by=user) | Q(tagged_users=user) | Q(service_providers=user) | Q(
            business_services__in=services)).distinct()

    return queryset


class NoteViewSet(mixins.ListModelMixin,

                  viewsets.GenericViewSet):
    serializer_class = NoteListSerializer
    pagination_class = NoteListPaginator

    def get_queryset(self):
        show_archieved = self.request.query_params.get('archieved', False)
        if show_archieved:
            show_archieved = show_archieved.lower() == 'true'

        queryset = get_note_queryset(self.request.user).filter(
            is_archieved=show_archieved
        )

        return queryset


class NoteDetailViewSet(mixins.CreateModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = NoteSerializer

    permission_classes = [IsCreator | IsGroupAdmin | IsListCreator]

    def get_queryset(self):
        return get_note_queryset(self.request.user)

    def get_object(self):
        queryset = self.get_queryset()

        params = self.kwargs['pk']
        try:
            params = int(params)
        except:
            pass
        if type(params) != int:
            self.kwargs = {'hashcode': params}

        obj = get_object_or_404(queryset, **self.kwargs)
        self.check_object_permissions(self.request, obj)

        return obj

    def perform_create(self, serializer):

        hashcode = self.request.data.get('hashcode', None)
        if hashcode == None or len(hashcode) == 0:
            raise ValidationError("Enter Hash Code")
        try:
            new_note = serializer.save(created_by=self.request.user, hashcode=hashcode)
        except Exception as e:
            raise ValidationError(e)

        task_id = self.request.data.get('task_id', None)

        if task_id != None:

            if type(task_id) == int:
                try:
                    task = Task.objects.get(id=task_id)
                except Task.DoesNotExist:
                    raise ValidationError('Task doesnt exist')
            else:
                try:
                    task = Task.objects.get(hashcode=task_id)
                except Task.DoesNotExist:
                    raise ValidationError('Task doesnt exist')
            if task.created_by != self.request.user:
                raise PermissionDenied("Permission Denied")
            new_note.task = task
        tagged_user_ids = self.request.data.get('tagged_users_id', None)

        if tagged_user_ids != None:

            tagged_users = list(User.objects.filter(id__in=tagged_user_ids))
            for users in tagged_users:
                if users != self.request.user:
                    new_note.tagged_users.add(users)

        group_user_ids = self.request.data.get('group_id', None)
        if group_user_ids != None:

            group_users = list(UserGroup.objects.filter(id__in=group_user_ids))

            for g_list in group_users:
                if g_list.classification == 0:
                    continue
                else:
                    new_note.user_groups.add(g_list)

        phone_number = self.request.data.get("phone_number", None)

        if phone_number != None:

            for no in phone_number:
                p = PhoneNumberField(no)
                try:
                    p.run_validators(no)
                except:
                    continue

                try:
                    user_name = User.objects.get(phone_number=no)
                    new_note.tagged_users.add(user_name)

                except User.DoesNotExist:

                    username = no

                    user = User(username=username, phone_number=no)
                    password = User.objects.make_random_password()

                    user.set_password(password)
                    user.save()
                    new_note.tagged_users.add(user)

    def perform_update(self, serializer):

        instance = serializer.save()
        tagged_user_ids = self.request.data.get('tagged_users_id', None)
        if tagged_user_ids != None:

            instance.tagged_users.clear()

            tagged_users = list(User.objects.filter(id__in=tagged_user_ids))
            for users in tagged_users:
                if users != self.request.user:
                    instance.tagged_users.add(users)


        group_user_ids = self.request.data.get('group_id', None)
        if group_user_ids != None:

            instance.user_groups.clear()

            group_users = list(UserGroup.objects.filter(id__in=group_user_ids))

            for g_list in group_users:
                if g_list.classification == 0:
                    continue
                else:
                    instance.user_groups.add(g_list)
        task_id = self.request.data.get('task_id', None)
        if task_id != None:
            if type(task_id) == int:
                try:
                    task = Task.objects.get(id=task_id)
                except Task.DoesNotExist:
                    raise ValidationError('Task doesnt exist')
            else:
                try:
                    task = Task.objects.get(hashcode=task_id)
                except Task.DoesNotExist:
                    raise ValidationError('Task doesnt exist')

            if task.created_by != self.request.user:
                raise PermissionDenied("Permission Denied")
            instance.task = task

        phone_number = self.request.data.get("phone_number", None)
        if phone_number != None:

            for no in phone_number:
                p = PhoneNumberField(no)
                try:
                    p.run_validators(no)  # for checking if a phone number is valid or not
                except:
                    continue
                try:
                    user_name = User.objects.get(phone_number=no)
                    instance.tagged_users.add(user_name)

                except User.DoesNotExist:

                    username = no

                    user = User(username=username, phone_number=no)
                    password = User.objects.make_random_password()

                    user.set_password(password)
                    user.save()
                    instance.tagged_users.add(user)
        instance = serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.created_by != request.user:
            raise PermissionDenied("Permisison Denied")
        instance.is_archieved = True
        instance.save()

        return Response(self.get_serializer(instance).data)


class CheckListDetailViewSet(mixins.CreateModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.DestroyModelMixin,
                             viewsets.GenericViewSet):
    serializer_class = ChecklistSerializer
    permission_classes = [IsCheckListCreator | IsInCheckList]

    def get_queryset(self):
        return ChecklistItem.objects.all()

    def get_object(self):
        queryset = self.get_queryset()

        params = self.kwargs['pk']
        try:
            params = int(params)
        except:
            pass
        if type(params) != int:
            self.kwargs = {'hashcode': params}

        obj = get_object_or_404(queryset, **self.kwargs)
        self.check_object_permissions(self.request, obj)

        return obj

    def perform_create(self, serializer):
        try:
            hashcode = self.request.data.get('hashcode', None)

            note_id = self.request.data.get('note_id', None)

            if type(note_id) == int:
                note = Note.objects.get(id=note_id)


            else:
                note = Note.objects.get(hashcode=note_id)

            user_list = note.tagged_users.all()
            user_list = user_list | User.objects.filter(id=note.created_by.id)
            for g in note.user_groups.all():
                user_list = user_list | g.users.all()
            user_list = user_list.distinct()
            if self.request.user not in user_list:
                raise PermissionDenied("Permission Denied")

            if note.checklist.all().count() >= 100:
                raise ValidationError("Max Limit Reached")

            position = self.request.data.get('position')
            list_items = note.checklist.all().filter(position__gte=position).order_by('-position')
            for items in list_items:
                items.position += 1
                items.save()

            new_checklist = serializer.save(note=note, hashcode=hashcode)
        except Exception as e:
            raise ValidationError(e)

    def perform_update(self, serializer):

        position = self.request.data.get('position', None)
        params = self.kwargs
        try:
            id = params['pk']
            checklist = ChecklistItem.objects.get(id=id)
        except:
            id = params['hashcode']
            checklist = ChecklistItem.objects.get(hashcode=id)

        if position != None:
            list_items = checklist.note.checklist.all().filter(position__gte=position).order_by('-position')

            for items in list_items:
                items.position += 1
                items.save()

        instance = serializer.save()

        note_id = self.request.data.get('note_id', None)
        if note_id != None:
            if type(note_id) == int:

                try:
                    note = Note.objects.get(id=note_id)
                except Note.DoesNotExist:
                    raise ValidationError("Note doesnt exist")
            else:
                try:
                    note = Note.objects.get(hashcode=note_id)
                except Exception as e:
                    raise ValidationError(e)

            if note.created_by != self.request.user:
                raise PermissionDenied("Permission Denied")
            instance.note = note

        instance.save()


class RecentViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):

    def get_serializer_class(self, *args, **kwargs):

        isTask = self.request.query_params.get('isTask', False)
        if isTask and isTask.lower() == 'true':
            return TaskListSerializer
        else:
            return NoteListSerializer

    def get_queryset(self):
        isTask = self.request.query_params.get('isTask', False)

        today = datetime.today()

        delta = timedelta(days=5)  # specify the date

        if isTask and isTask.lower() == 'true':
            queryset = get_task_queryset(self.request.user).filter(is_archieved=False).order_by('-start_time')
        else:
            queryset = get_note_queryset(self.request.user).filter(is_archieved=False)

        queryset = queryset.filter(updated_at__gte=today.date() - delta).filter(
            updated_at__lte=today.date() + timedelta(days=1))
        return queryset


class RecentlyTaggedViewSet(mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = UserSerializer
    pagination_class = NoteListPaginator

    def list(self, request):
        user = self.request.user
        groups = user.user_groups.all()
        today = datetime.today()
        delta = timedelta(days=5)
        u = User.objects.none()
        g = UserGroup.objects.none()

        taskset = Task.objects.filter(Q(user_groups__in=groups) | Q(created_by=user) | Q(tagged_users=user)).distinct()
        # taskset = taskset.filter(is_archieved=False).order_by('-start_time')
        taskset = taskset.filter(updated_at__lte=today.date()).filter(updated_at__gte=today.date() - delta)

        for q in taskset:
            u = u | q.tagged_users.all()
            g = g | q.user_groups.all()

        noteset = Note.objects.filter(Q(user_groups__in=groups) | Q(created_by=user) | Q(tagged_users=user)).distinct()
        # note_set = noteset.filter(is_archieved=False).order_by('-start_time')
        noteset = noteset.filter(updated_at__lte=today.date()).filter(updated_at__gte=today.date() - delta)
        for q in noteset:
            u = u | q.tagged_users.all()
            g = g | q.user_groups.all()

        u = u.distinct()
        u = u.exclude(username=user.username)
        g = g.distinct()
        user_list = []
        group_list = []
        for lists in u:
            user_list.append(UserSerializer(lists).data)
        for lists in g:
            group_list.append(UserMaskGroupSerializer(lists).data)

        final_response = {}
        final_response["users"] = user_list
        final_response["user_groups"] = group_list
        return Response(final_response)


class RecentUserViewSet(mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    pagination_class = NoteListPaginator

    def get_serializer_class(self, *args, **kwargs):

        isTask = self.request.query_params.get('isTask', False)
        if isTask and isTask.lower() == 'true':
            return TaskListSerializer
        else:
            return NoteListSerializer

    def list(self, request, *args, **kwargs):
        isTask = self.request.query_params.get('isTask', False)
        phone_number = self.request.query_params.get('phone_number', None)
        phone_number = list(phone_number)
        phone_number[0] = '+'
        phone_number = ''.join(phone_number)
        final_response = {}
        if phone_number == None:
            raise ValidationError("Enter Phone number")

        user = User.objects.get(phone_number=phone_number)

        today = datetime.today()

        if isTask and isTask.lower() == 'true':
            queryset = get_task_queryset(self.request.user).filter(is_archieved=False).order_by('-start_time')
            queryset = queryset.filter(tagged_users=user.id)
            queryset_completed = queryset.filter(end_time__lte=today)
            queryset_upcoming = queryset.filter(start_time__gte=today)
            results = {}
            results["upcomming_tasks"] = self.get_serializer(queryset_upcoming, many=True).data
            results["completed_tasks"] = self.get_serializer(queryset_completed, many=True).data
            final_response["tasks"] = results
            return Response(final_response)


        else:
            queryset = get_note_queryset(self.request.user).filter(is_archieved=False)
            queryset = queryset.filter(tagged_users=user.id)

            final_response["notes"] = self.get_serializer(queryset, many=True).data

            return Response(final_response)


class RecentUserGroupViewSet(mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    pagination_class = NoteListPaginator

    def get_serializer_class(self, *args, **kwargs):

        isTask = self.request.query_params.get('isTask', False)
        if isTask and isTask.lower() == 'true':
            return TaskListSerializer
        else:
            return NoteListSerializer

    def get_queryset(self):
        try:
            isTask = self.request.query_params.get('isTask', False)
            group_id = self.request.query_params.get('group_id', None)

            group = UserGroup.objects.get(id=group_id)

            if isTask and isTask.lower()=='true':
                queryset=get_task_queryset(self.request.user).filter(is_archieved=False).order_by('-start_time')
                queryset=queryset.filter(user_groups=group)
                return queryset
            else:
                queryset=get_note_queryset(self.request.user).filter(is_archieved=False)
                queryset=queryset.filter(user_groups=group)
                return queryset
        except Exception as e:
            raise ValidationError(e)

