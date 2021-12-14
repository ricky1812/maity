import datetime as dt
from datetime import date, datetime

import pytz
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import viewsets, mixins, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from business.models import Business
from business.service.models import Service
from note.permissions import IsCreator, IsListCreator
from note.task.models import Task, SubTasks, FeedbackTags
from note.task.paginators import TaskListPaginator
from note.task.serializers import TaskSerializer, TaskListSerializer, AppointmentListSerializer, FeedBackTagSerializer, \
    FeedBackSerializer
from user.models import UserGroup, User
from user.permissions import IsGroupAdmin

import json

from user.serializers import UserSerializer
from utility.helpers import TimestampField

from phonenumber_field.modelfields import PhoneNumberField

utc = pytz.UTC

# ...........
import urllib.request
import urllib.parse


def sendSMS(apikey, numbers, sender, message):
    data = urllib.parse.urlencode({'apikey': 'ZmE3NmJlZjQxZWZmZTlmNWY5ZjFjOTRkNDE5YjQ4Y2M=', 'numbers': numbers,
                                   'message': "hey there", 'sender': "pointapp"})

    data = data.encode('utf-8')
    request = urllib.request.Request("https://api.textlocal.in/send/")
    f = urllib.request.urlopen(request, data)
    fr = f.read()
    return (fr)


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


class TaskViewSet(mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    serializer_class = TaskListSerializer
    pagination_class = TaskListPaginator

    def get_queryset(self):
        show_archieved = self.request.query_params.get('archieved', False)
        show_type = self.request.query_params.get('show_type', None)
        isPrev = self.request.query_params.get('isPrev', False)

        if isPrev and isPrev.lower() == 'true':
            if show_archieved:
                show_archieved = show_archieved.lower() == 'true'
            today = date.today()
            queryset = get_task_queryset(self.request.user).filter(
                is_archieved=show_archieved
            ).filter(
                start_time__lte=today
            ).order_by('-start_time')


        else:
            if show_archieved:
                show_archieved = show_archieved.lower() == 'true'
            today = date.today()
            queryset = get_task_queryset(self.request.user).filter(
                is_archieved=show_archieved
            ).filter(
                start_time__gte=today
            )
        if show_type != None:
            queryset = queryset.filter(status=show_type)

        return queryset


class TaskDetailViewSet(mixins.CreateModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsCreator | IsGroupAdmin | IsListCreator]

    def get_queryset(self):
        return get_task_queryset(self.request.user)

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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.created_by != request.user:
            raise PermissionDenied("Permisison Denied")
        instance.is_archieved = True
        instance.save()

        return Response(self.get_serializer(instance).data)

    def perform_create(self, serializer):
        show_type = int(self.request.data.get('show_type', 0))
        hashcode = self.request.data.get("hashcode", None)
        try:
            new_task = serializer.save(created_by=self.request.user, status=show_type, hashcode=hashcode)
        except Exception as e:
            raise ValidationError(e)
        tagged_user_ids = self.request.data.get('tagged_users_id', None)

        if tagged_user_ids != None:
            tagged_users = list(User.objects.filter(id__in=tagged_user_ids))
            new_task.tagged_users.add(*tagged_users)
        group_user_ids = self.request.data.get('group_id', None)
        if group_user_ids != None:

            group_users = list(UserGroup.objects.filter(id__in=group_user_ids))

            for g_list in group_users:
                if g_list.classification == 0:
                    continue
                else:
                    new_task.user_groups.add(g_list)

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
                    new_task.tagged_users.add(user_name)

                except User.DoesNotExist:

                    username = no

                    user = User(username=username, phone_number=no)
                    password = User.objects.make_random_password()

                    user.set_password(password)
                    user.save()
                    new_task.tagged_users.add(user)
        # ..................................................................................................
        # appointments

        if show_type == 1:
            service_id = self.request.data.get('service_id', None)
            if service_id == None or len(service_id) == 0:
                raise ValidationError("Service doesnt exist")
            try:
                service = Service.objects.get(id=service_id)
            except Service.DoesNotExist:
                raise ValidationError("Service doesnt exist")
            new_task.business_services.add(service)
            if tagged_user_ids == None and group_user_ids == None:
                provider_id = int(self.request.data.get('provider_id'))

                new_task.service_providers.add(User.objects.get(id=provider_id))
                new_task.end_time = new_task.start_time + service.duration
                new_task.save()
            else:

                users = new_task.tagged_users.all()
                groups = new_task.user_groups.all()
                for g in groups:
                    users = users | g.users.all()
                users = users.distinct()
                count = users.count()
                providers = service.business.group.users.all()

                s_h = new_task.start_time  # start hour
                s_h = utc.localize(s_h)  # ..............localising time
                e_h = service.business.timeslots.all().get(day=s_h.weekday() + 1)  # ending hour of business
                e_h = datetime.combine(e_h.end_date, e_h.end_time)
                e_h = utc.localize(e_h)
                end = e_h  # end hour
                delta = dt.timedelta(minutes=30)
                provider_mat = [[] for _ in range(providers.count())]  # provider matrix for storing time
                for i in range(0, providers.count()):  # initialising the matrix
                    time = providers[i].subtask_provider.all()
                    for t in time:
                        provider_mat[i].append([t.start, t.end])

                while (s_h <= e_h):
                    if count <= 0:
                        break
                    j = 0
                    while (j < providers.count() and count > 0):

                        flag = 0
                        try:
                            sub_t = providers[j].subtask_provider.all().get(start=s_h)

                        except SubTasks.DoesNotExist:
                            interval = [s_h, s_h + service.duration]
                            provider_mat[j].sort()

                            if len(provider_mat[j]) == 0:

                                provider_mat[j].append(interval)

                                flag = 1

                            elif interval[1] <= provider_mat[j][0][0]:

                                provider_mat[j].append(interval)
                                flag = 1
                            elif interval[0] >= provider_mat[j][-1][1]:

                                provider_mat[j].append(interval)
                                flag = 1

                            else:
                                for t in range(0, len(provider_mat[j]) - 1):
                                    if s_h >= provider_mat[j][t][1] and s_h + service.duration <= \
                                            provider_mat[j][t + 1][0]:
                                        flag = 1

                                        provider_mat[j].append(interval)

                            if flag == 1:
                                count -= 1

                                end = s_h + service.duration
                                subtask = SubTasks.objects.create(start=s_h, task=new_task, provider=providers[j],
                                                                  end=end)
                                new_task.service_providers.add(providers[j])
                        j += 1
                    s_h = s_h + delta
                new_task.end_time = end
                new_task.save()

    def perform_update(self, serializer):
        instance = serializer.save()
        tagged_user_ids = self.request.data.get('tagged_users_id', None)
        if tagged_user_ids != None:
            instance.tagged_users.clear()

            tagged_users = list(User.objects.filter(id__in=tagged_user_ids))
            instance.tagged_users.add(*tagged_users)
        group_user_ids = self.request.data.get('group_id', None)
        if group_user_ids != None:
            instance.user_groups.clear()

            group_users = list(UserGroup.objects.filter(id__in=group_user_ids))

            for g_list in group_users:
                if g_list.classification == 0:
                    continue
                else:
                    instance.user_groups.add(g_list)
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
                    # resp = sendSMS('OGZkZGJiNjExMThlNzRkM2M0MGE0ZDYzZjk2MDc4YmI=', no,
                    #               'Jims Autos', 'This is your message')
                    # print(resp)


class ServiceProviderViewSet(mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    serializer_class = AppointmentListSerializer
    pagination_class = TaskListPaginator

    def get_serializer_context(self):
        context = super(ServiceProviderViewSet, self).get_serializer_context()
        date_id = self.request.query_params.get("date_id", None)
        if date_id == None or len(date_id) == 0:
            raise ValidationError("Enter Date")

        context.update({"request": date_id})
        return context

    def get_queryset(self):
        business_id = self.request.query_params.get('business_id', None)

        if business_id == None:
            raise ValidationError("Business Id is not given")
        business_id = int(business_id)
        try:
            business = Business.objects.get(id=business_id)
        except Business.DoesNotExist:
            raise ValidationError('Business doesnt exist')

        return business.group.users.all()


# ...............................................................

class AppointmentDetailViewSet(mixins.CreateModelMixin,

                               mixins.RetrieveModelMixin,
                               viewsets.GenericViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsCreator | IsGroupAdmin | IsListCreator]

    def get_queryset(self):
        return get_task_queryset(self.request.user)

    def create(self, request, *args, **kwargs):
        data_total = request.data
        final_response = {}
        result = []
        for data in data_total:
            show_type = 1
            try:

                new_task = self.get_serializer(data=data)
                new_task.is_valid(raise_exception=True)
                new_task = new_task.save(created_by=self.request.user, status=show_type)
            except Exception as e:
                raise ValidationError(e)

            tagged_user_ids = data['tagged_users_ids']

            if tagged_user_ids != None:
                tagged_users = list(User.objects.filter(id__in=tagged_user_ids))
                new_task.tagged_users.add(*tagged_users)
            group_user_ids = data['group_id']
            if group_user_ids != None:

                group_users = list(UserGroup.objects.filter(id__in=group_user_ids))

                for g_list in group_users:
                    if g_list.classification == 0:
                        continue
                    else:
                        new_task.user_groups.add(g_list)

            phone_number = data["phone_number"]
            if phone_number != None:

                for no in phone_number:
                    p = PhoneNumberField(no)
                    try:
                        p.run_validators(no)
                    except:
                        continue

                    try:
                        user_name = User.objects.get(phone_number=no)
                        new_task.tagged_users.add(user_name)

                    except User.DoesNotExist:

                        username = no

                        user = User(username=username, phone_number=no)
                        password = User.objects.make_random_password()

                        user.set_password(password)
                        user.save()
                        new_task.tagged_users.add(user)

            service_id = data['service_id']

            if service_id == None:
                raise ValidationError("Enter Service Id")
            try:
                service = Service.objects.get(id=service_id)

            except Service.DoesNotExist:
                raise ValidationError("Service doesnt exist")

            new_task.business_services.add(service)
            provider_id = data['provider_id']

            if len(provider_id) != 0:

                provider = User.objects.get(id=provider_id)

                new_task.service_providers.add(User.objects.get(id=provider_id))
                new_task.end_time = new_task.start_time + service.duration
                subtask = SubTasks.objects.create(start=new_task.start_time, task=new_task, provider=provider,
                                                  end=new_task.start_time + service.duration)

                new_task.service_providers.add(provider)

                new_task.save()
                result.append({"data": TaskSerializer(new_task).data})
            else:

                users = new_task.tagged_users.all()
                groups = new_task.user_groups.all()
                for g in groups:
                    users = users | g.users.all()
                users = users.distinct()
                count = users.count()
                providers = service.business.group.users.all()
                providers = list(providers)

                s_h = new_task.start_time  # start hour
                s_h = utc.localize(s_h)  # ..............localising time
                e_h = service.business.timeslots.all().get(day=s_h.weekday() + 1)  # ending hour of business
                e_h = datetime.combine(s_h.date(), e_h.end_time)
                e_h = utc.localize(e_h)
                end = e_h  # end hour
                delta = dt.timedelta(minutes=15)
                provider_mat = [[] for _ in range(len(providers))]  # provider matrix for storing time
                for i in range(0, len(providers)):  # initialising the matrix
                    time = providers[i].subtask_provider.all()
                    for t in time:
                        provider_mat[i].append([t.start, t.end])

                while (s_h < e_h):

                    if count <= 0:
                        break
                    j = 0
                    while (j < len(providers) and count > 0):

                        flag = 0

                        try:
                            sub_t = providers[j].subtask_provider.all().get(start=s_h)

                        except SubTasks.DoesNotExist:
                            interval = [s_h, s_h + service.duration]
                            provider_mat[j].sort()

                            if len(provider_mat[j]) == 0:

                                provider_mat[j].append(interval)

                                flag = 1

                            elif interval[1] <= provider_mat[j][0][0]:

                                provider_mat[j].append(interval)
                                flag = 1
                            elif interval[0] >= provider_mat[j][-1][1]:

                                provider_mat[j].append(interval)
                                flag = 1

                            else:
                                for t in range(0, len(provider_mat[j]) - 1):
                                    if s_h >= provider_mat[j][t][1] and s_h + service.duration <= \
                                            provider_mat[j][t + 1][0]:
                                        flag = 1

                                        provider_mat[j].append(interval)

                            if flag == 1:
                                count -= 1

                                end = s_h + service.duration
                                subtask = SubTasks.objects.create(start=s_h, task=new_task, provider=providers[j],
                                                                  end=end)

                                new_task.service_providers.add(providers[j])
                        j += 1
                    s_h = s_h + delta
                new_task.end_time = end

                new_task.save()

                result.append({"data": TaskSerializer(new_task).data})
        final_response["result"] = result
        return Response(final_response)


class Calculate(APIView):

    def post(self, request):

        data = self.request.data
        final_response = {}
        result = []
        # checklist = []
        business_id = data[0]["business_id"]
        business = Business.objects.get(id=business_id)
        start_time = data[0]["start_time"]
        start_time = dt.datetime.utcfromtimestamp(start_time / 1000)

        providers = list(business.group.users.all())
        provider_mat = [[] for _ in range(len(providers))]
        for i in range(0, len(providers)):
            time = providers[i].subtask_provider.all().filter(start__date=start_time.date())
            for t in time:
                provider_mat[i].append([t.start, t.end])
            provider_mat[i].sort()

        for i in range(0, len(data)):
            checklist = []

            business_id = data[i]["business_id"]
            service_id = data[i]["service_id"]
            tagged_users = data[i]["tagged_users_ids"]
            group_id = data[i]["group_id"]
            count = 0
            user_set = {}
            user_set = set()

            user_list = list(User.objects.filter(id__in=tagged_users).values_list('phone_number', flat=True))
            user_set.update(user_list)

            for id in group_id:
                group = UserGroup.objects.get(id=id)
                # user_list = user_list | group.users.all()
                user_list = list(group.users.all().values_list('phone_number', flat=True))
                user_set.update(user_list)

            phone_number = data[i]["phone_number"]
            if phone_number != None:

                for no in phone_number:
                    p = PhoneNumberField(no)
                    try:
                        p.run_validators(no)
                    except:
                        continue

                    user_set.add(no)

            count = len(user_set)

            start_time = data[i]["start_time"]
            start_time = dt.datetime.utcfromtimestamp(start_time / 1000)

            business = Business.objects.get(id=business_id)
            service = Service.objects.get(id=service_id)
            # ...................................

            s_h = start_time
            s_h = utc.localize(s_h)

            e_h = service.business.timeslots.all().get(day=s_h.weekday() + 1)  # end time
            e_h = datetime.combine(s_h.date(), e_h.end_time)
            e_h = utc.localize(e_h)

            end = e_h
            delta = dt.timedelta(minutes=15)
            check = dt.timedelta(minutes=15)
            provider_id = data[i]["provider_id"]

            if len(provider_id) != 0 and count == 1:

                provider = User.objects.get(id=provider_id)
                index = 0
                for p in range(0, len(providers)):
                    if (providers[p] == provider):
                        break
                    index = index + 1

                flag = 0

                interval = [s_h, s_h + service.duration]
                provider_mat[index].sort()
                if len(provider_mat[index]) == 0:
                    provider_mat[index].append(interval)
                    result.append({"time": [interval[0].timestamp() * 1000, interval[1].timestamp() * 1000],
                                   "provider": UserSerializer(provider).data})
                    flag = 1
                    checklist.append([interval[0], interval[1]])

                elif interval[1] <= provider_mat[index][0][0]:
                    flag = 1
                    provider_mat[index].append(interval)
                    result.append({"time": [interval[0].timestamp() * 1000, interval[1].timestamp() * 1000],
                                   "provider": UserSerializer(provider).data})
                    checklist.append([interval[0], interval[1]])
                elif interval[0] >= provider_mat[index][-1][1]:
                    flag = 1
                    provider_mat[index].append(interval)
                    result.append({"time": [interval[0].timestamp() * 1000, interval[1].timestamp() * 1000],
                                   "provider": UserSerializer(provider).data})
                    checklist.append([interval[0], interval[1]])
                else:
                    for t in range(0, len(provider_mat[index]) - 1):
                        if s_h >= provider_mat[index][t][1] and s_h + service.duration <= \
                                provider_mat[index][t + 1][0]:
                            flag = 1
                            provider_mat[index].append(interval)
                            result.append({"time": [interval[0].timestamp() * 1000, interval[1].timestamp() * 1000],
                                           "provider": UserSerializer(provider).data})
                            checklist.append([interval[0], interval[1]])
                if flag == 0:
                    final_response["timeslots"] = "None"
                    final_response["check"] = False
                    final_response["error"] = "Providers not available"
                    return HttpResponse(json.dumps(final_response), "application/json")


            else:

                flag = 0

                # .................calculation

                while (s_h <= e_h):
                    if count <= 0:
                        break
                    j = 0
                    while (j < len(providers) and count > 0):
                        flag = 0
                        interval = [s_h, s_h + service.duration]

                        if len(provider_mat[j]) == 0:
                            provider_mat[j].append(interval)
                            result.append({"time": [interval[0].timestamp() * 1000, interval[1].timestamp() * 1000],
                                           "provider": UserSerializer(providers[j]).data})
                            checklist.append([interval[0], interval[1]])
                            flag = 1
                        elif interval[1] <= provider_mat[j][0][0]:

                            provider_mat[j].insert(0, interval)
                            result.append({"time": [interval[0].timestamp() * 1000, interval[1].timestamp() * 1000],
                                           "provider": UserSerializer(providers[j]).data})
                            checklist.append([interval[0], interval[1]])
                            flag = 1
                        elif interval[0] >= provider_mat[j][-1][1]:
                            provider_mat[j].append(interval)
                            result.append({"time": [interval[0].timestamp() * 1000, interval[1].timestamp() * 1000],
                                           "provider": UserSerializer(providers[j]).data})
                            checklist.append([interval[0], interval[1]])
                            flag = 1
                        else:
                            for t in range(0, len(provider_mat[j]) - 1):
                                if s_h >= provider_mat[j][t][1] and s_h + service.duration <= \
                                        provider_mat[j][t + 1][0]:
                                    flag = 1

                                    provider_mat[j].insert(t + 1, interval)  # check.................
                                    result.append(
                                        {"time": [interval[0].timestamp() * 1000, interval[1].timestamp() * 1000],
                                         "provider": UserSerializer(providers[j]).data})
                                    checklist.append([interval[0], interval[1]])
                        if flag == 1:
                            count -= 1

                            end = s_h + service.duration
                        j += 1

                    s_h = s_h + delta

                if (count > 0):
                    final_response["timeslots"] = "None"
                    final_response["check"] = False
                    final_response["error"] = "Providers not available"
                    return HttpResponse(json.dumps(final_response), "application/json")

                for i in range(1, len(checklist)):
                    if checklist[i][0] > checklist[i - 1][1] and checklist[i][0] - checklist[i - 1][1] > check:
                        final_response["timeslots"] = "None"
                        final_response["check"] = False
                        final_response["error"] = "Continous slot not available"
                        return HttpResponse(json.dumps(final_response), "application/json")
                check_time = utc.localize(start_time)
                if checklist[0][0] != check_time:
                    final_response["timeslots"] = result
                    final_response["check"] = False
                    final_response["error"] = "The slot has been blocked"
                    return HttpResponse(json.dumps(final_response), "application/json")

            final_response["timeslots"] = result
            final_response["check"] = True
            final_response["error"] = "None"

            return HttpResponse(json.dumps(final_response), "application/json")


class FreeTimeViewset(mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    def list(self, request):
        business_id = self.request.query_params.get("business_id", None)
        date_id = self.request.query_params.get("date_id", None)
        date_id = datetime.utcfromtimestamp(float(date_id) / 1000.0).date()
        business = Business.objects.get(id=business_id)
        providers = business.group.users.all()
        providers = list(providers)

        provider_mat = [[] for _ in range(len(providers))]
        for i in range(0, len(providers)):

            time = providers[i].subtask_provider.all().filter(start__date=date_id)
            for t in time:
                provider_mat[i].append([t.start, t.end])

        timeslot = business.timeslots.all().get(day=date_id.weekday() + 1)

        current_time = datetime.now()
        if current_time.date() == date_id:
            s_h = current_time + dt.timedelta(minutes=30)
        else:
            s_h = datetime.combine(date_id, timeslot.start_time)
        s_h = utc.localize(s_h)
        e_h = datetime.combine(date_id, timeslot.end_time)
        e_h = utc.localize(e_h)

        delta = dt.timedelta(minutes=15)

        free_time = []

        while (s_h < e_h):
            j = 0
            free_providers = []
            while (j < len(providers)):
                flag = 0

                try:
                    sub_t = providers[j].subtask_provider.all().get(start=s_h)

                except SubTasks.DoesNotExist:
                    interval = [s_h, s_h + delta]
                    provider_mat[j].sort()
                    if len(provider_mat[j]) == 0:

                        free_providers.append(providers[j].id)

                    elif interval[1] <= provider_mat[j][0][0]:
                        free_providers.append(providers[j].id)

                    elif interval[0] >= provider_mat[j][-1][1]:
                        free_providers.append(providers[j].id)

                    else:
                        for t in range(0, len(provider_mat[j]) - 1):
                            if s_h >= provider_mat[j][t][1] and s_h + delta <= \
                                    provider_mat[j][t + 1][0]:
                                free_providers.append(providers[j].id)

                j += 1

            if len(free_providers) > 0:
                free_time.append({"time": [s_h.time(), s_h.timestamp() * 1000, (s_h + delta).timestamp() * 1000],
                                  "providers": free_providers})
            s_h = s_h + delta

        final_response = {}
        final_response["response"] = free_time

        return Response(final_response)


def checkFreeTime(business_id, date_id):
    business = Business.objects.get(id=business_id)
    providers = list(business.group.users.all())
    calc = [0] * 96
    provider_mat = [[] for _ in range(len(providers))]

    timeslot = business.timeslots.all().get(day=date_id.weekday() + 1)
    s_h = datetime.combine(date_id, timeslot.start_time)
    s_h = utc.localize(s_h)
    e_h = datetime.combine(date_id, timeslot.end_time)
    e_h = utc.localize(e_h)

    delta = dt.timedelta(minutes=15)
    block_time = []
    current_time = datetime.now()
    time = current_time + dt.timedelta(minutes=30)
    time = utc.localize(time)

    if date_id == current_time.date() and time >= s_h:
        if time >= e_h:
            block_time.append([s_h.timestamp() * 1000, e_h.timestamp() * 1000])
            s_h = e_h
        else:

            block_time.append([s_h.timestamp() * 1000, time.timestamp() * 1000])
            s_h = current_time + dt.timedelta(minutes=30)
            s_h = utc.localize(s_h)

    initial_time = time.replace(hour=0, minute=0, second=0)

    for i in range(0, len(providers)):
        time = providers[i].subtask_provider.all().filter(start__date=date_id)

        for t in time:

            provider_mat[i].append([t.start, t.end])
            start_time = t.start
            end_time = t.end

            initial_time = start_time.replace(hour=0, minute=0, second=0)
            diff1 = (start_time - initial_time).total_seconds() / 60  # diff in minute
            diff2 = (end_time - initial_time).total_seconds() / 60
            index1 = int(diff1 / 15)
            index2 = int(diff2 / 15)

            for indx in range(index1, index2):
                calc[indx] = calc[indx] + 1

    count = len(providers)

    for ind in range(0, 96):
        if calc[ind] == count:
            diff = ind * 15 * 60  # in seconds
            diff = dt.timedelta(seconds=diff)
            start_time = initial_time + diff
            end_time = start_time + dt.timedelta(minutes=15)

            block_time.append([start_time.timestamp() * 1000, end_time.timestamp() * 1000])

    return block_time


class FreeServiceProviderViewSet(mixins.ListModelMixin,
                                 viewsets.GenericViewSet):
    serializer_class = UserSerializer
    pagination_class = TaskListPaginator

    def get_queryset(self):
        business_id = self.request.query_params.get('business_id', None)

        if business_id == None:
            raise ValidationError("Business Id is not given")
        business_id = int(business_id)
        try:
            business = Business.objects.get(id=business_id)
        except Business.DoesNotExist:
            raise ValidationError('Business doesnt exist')

        date_id = self.request.query_params.get("date_id", None)

        if date_id == None or len(date_id) == 0:
            raise ValidationError('Enter Date')

        service_id = self.request.query_params.get('service_id', None)
        if service_id == None or len(service_id) == 0:
            raise ValidationError('Enter Service id')

        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            raise ValidationError('Service does not exist')

        date_id = datetime.utcfromtimestamp(float(date_id) / 1000.0)

        providers = business.group.users.all()
        provider_mat = [[] for _ in range(providers.count())]
        for i in range(0, providers.count()):
            time = providers[i].subtask_provider.all().filter(start__date=date_id.date())
            for t in time:
                provider_mat[i].append([t.start, t.end])

        free_providers = []

        s_h = date_id
        s_h = utc.localize(s_h)
        e_h = s_h + service.duration

        delta = dt.timedelta(minutes=30)
        j = 0
        queryset = User.objects.none()
        while (j < providers.count()):
            try:
                sub_t = providers[j].subtask_provider.all().get(start=s_h)

            except SubTasks.DoesNotExist:
                interval = [s_h, e_h]
                provider_mat[j].sort()

                if len(provider_mat[j]) == 0:
                    free_providers.append(providers[j].id)

                elif interval[1] <= provider_mat[j][0][0]:
                    free_providers.append(providers[j].id)

                elif interval[0] >= provider_mat[j][-1][1]:
                    free_providers.append(providers[j].id)

                else:
                    for t in range(0, len(provider_mat[j]) - 1):
                        if s_h >= provider_mat[j][t][1] and e_h <= \
                                provider_mat[j][t + 1][0]:
                            free_providers.append(providers[j].id)
            j += 1
        queryset = User.objects.none()
        for id in free_providers:
            prov = User.objects.filter(id=id)
            queryset = queryset | prov

        return queryset


class RecentAppointmentViewSet(mixins.RetrieveModelMixin,

                               viewsets.GenericViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        user = self.request.user
        return get_task_queryset(user).filter(status=1)

    def list(self, request, *args, **kwargs):
        final_response = {}
        id = self.request.query_params.get('appointment_id', None)

        delta = dt.timedelta(minutes=30)
        current_time = datetime.now()
        queryset = self.get_queryset().filter(end_time__lte=current_time - delta).filter(
            start_time__gte=current_time - dt.timedelta(days=1))

        if len(queryset) == 0:
            final_response["result"] = False
            final_response["data"] = "Null"
            final_response["tags"] = "Null"
            return Response(final_response)
        else:
            value = list(queryset)[-1]
            if id != None:
                if type(id) != int:
                    id = int(id)

            if id != None and value.id == id:
                final_response["result"] = False
                final_response["data"] = "Null"
                final_response["tags"] = "Null"


            else:
                final_response["result"] = True
                final_response["data"] = self.get_serializer(value).data
                service = list(value.business_services.all())[0]
                business_category = service.business.category
                tags = FeedbackTags.objects.filter(category=business_category)
                final_response["tags"] = FeedBackTagSerializer(tags, many=True).data

            return Response(final_response)


class FeedBackTagsViewset(mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    pagination_class = TaskListPaginator
    serializer_class = FeedBackTagSerializer

    def get_queryset(self):
        business_id = self.request.query_params.get("business_id", None)
        if business_id == None or len(business_id) == 0:
            raise ValidationError("Enter Business Id")
        try:
            business = Business.objects.get(id=business_id)
        except Business.DoesNotExist:
            raise ValidationError("Business doesn not exist")
        category = business.category

        return FeedbackTags.objects.filter(category=category)


class FeedbackViewSet(mixins.RetrieveModelMixin,
                      mixins.CreateModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = FeedBackSerializer

    def perform_create(self, serializer):
        business_id = self.request.data.get("business_id", None)
        provider_id = self.request.data.get("provider_id", None)
        tags_id = self.request.data.get("tags_id", None)
        task_id = self.request.data.get("task_id", None)

        try:
            business = Business.objects.get(id=business_id)
            provider = User.objects.get(id=provider_id)
            task = Task.objects.get(id=task_id)
            new_feedback = serializer.save(provider=provider, business=business, user=self.request.user, task=task)
        except Exception as e:
            raise ValidationError(e)

        if tags_id != None:
            tags = list(FeedbackTags.objects.filter(id__in=tags_id))

            new_feedback.feedback_tags.add(*tags)
        new_feedback.save()
