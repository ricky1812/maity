import hashlib
from decouple import config

from django.db.models import Q
from rest_framework import viewsets, mixins
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from user.models import User, UserGroup
from user.serializers import UserGroupSerializer, UserDetailSerializer, UserGroupDetailSerializer, \
    MyTokenObtainPairSerializer, UserSerializer
from utility.do_spaces import get_upload_presigned_url, get_download_presigned_url, list_presigned_url
from .paginators import UserListPaginator
from .permissions import *
from rest_framework.response import Response
from phonenumber_field.modelfields import PhoneNumberField
import datetime as dt
from datetime import datetime
from cryptography.fernet import Fernet

SPACES_URL='https://assets.pointapp.in/'
WEBSOCKET_URL='wss://api.staging.pointapp.in/ws/tasks/'


def get_user_queryset(user: User):
    user = user
    queryset = UserGroup.objects.filter(Q(users__id=user.id) | Q(group_admin=user)).distinct()

    return queryset


class UserGroupViewSet(mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    serializer_class = UserGroupSerializer
    pagination_class = UserListPaginator

    def get_queryset(self):
        return get_user_queryset(self.request.user)


class MyCreatedUserGroupViewSet(mixins.ListModelMixin,
                                viewsets.GenericViewSet):
    serializer_class = UserGroupSerializer
    pagination_class = UserListPaginator

    def get_queryset(self):
        return get_user_queryset(self.request.user).filter(group_admin=self.request.user)


class UserGroupDetailViewSet(mixins.CreateModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             viewsets.GenericViewSet):
    serializer_class = UserGroupDetailSerializer

    def get_queryset(self):
        return get_user_queryset(self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        remove_id = self.request.data.get('remove_id', None)
        if remove_id != None:

            users = User.objects.filter(id__in=remove_id)
            users = list(users)
            group = UserGroup.objects.get(id=instance.id)
            for user_list in users:
                user_list.user_groups.remove(group)

        add_id = self.request.data.get('add_id', None)
        if add_id != None:

            users = User.objects.filter(id__in=add_id)
            users = list(users)
            group = UserGroup.objects.get(id=instance.id)
            for user_list in users:
                user_list.user_groups.add(group)

    def create(self, request, *args, **kwargs):
        user_ids = self.request.data.get('user_ids', None)
        group_ids = self.request.data.get('group_ids', None)

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
                    user_ids.append(user_name.id)

                except User.DoesNotExist:

                    username = no

                    user = User(username=username, phone_number=no)
                    password = User.objects.make_random_password()

                    user.set_password(password)
                    user.save()
                    user_ids.append(user.id)

        if len(group_ids) == 1 and len(user_ids) == 0:
            group = UserGroup.objects.get(id=group_ids[0])
            return Response(self.get_serializer(group).data)

        user_list = User.objects.filter(id__in=user_ids)

        group_list = UserGroup.objects.filter(id__in=group_ids)
        for group in group_list:
            if group.group_admin != self.request.user:
                raise PermissionDenied("Permission denied")
            user_list = user_list | group.users.all()
        user_list = user_list.distinct()

        new_group = self.get_serializer(data=request.data)
        new_group.is_valid(raise_exception=True)
        new_group = new_group.save(group_admin=self.request.user)
        new_group.users.add(*user_list)
        new_group.save()
        return Response(self.get_serializer(new_group).data)


class UserViewSet(mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    serializer_class = UserSerializer
    pagination_class = UserListPaginator

    def get_queryset(self):
        user = self.request.user
        groups = user.user_groups.all()
        notes = Note.objects.filter(Q(user_groups__in=groups) | Q(created_by=user) | Q(tagged_users=user)).distinct()
        tasks = Task.objects.filter(Q(user_groups__in=groups) | Q(created_by=user) | Q(tagged_users=user)).distinct()
        users = Note.objects.none()
        for n in notes:
            users = users | n.tagged_users.all()
        for t in tasks:
            users = users | t.tagged_users.all()
        users = users.distinct()
        return users


class UserDetailViewSet(mixins.UpdateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = UserDetailSerializer
    permission_classes = [IsUser]

    def get_queryset(self):
        user = self.request.user
        users = User.objects.all().filter(id=user.id)
        return users

    def perform_update(self, serializer):
        instance = serializer.save()


class UserCommonGroupViewSet(mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    serializer_class = UserGroupSerializer
    pagination_class = UserListPaginator

    def get_queryset(self):
        user = self.request.user
        groups = user.user_groups.all()
        notes = Note.objects.filter(Q(user_groups__in=groups) | Q(created_by=user) | Q(tagged_users=user)).distinct()
        tasks = Task.objects.filter(Q(user_groups__in=groups) | Q(created_by=user) | Q(tagged_users=user)).distinct()
        groups = Note.objects.none()
        for n in notes:
            groups = groups | n.user_groups.all()
        for t in tasks:
            groups = groups | t.user_groups.all()
        groups = groups.distinct()
        return groups


class UserExitViewSet(mixins.ListModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = UserGroupSerializer

    def get_queryset(self):
        return get_user_queryset(self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        user = self.request.user
        user.user_groups.remove(instance.id)


class UserImageView(APIView):
    def get(self, request):
        user = self.request.user
        id = user.id

        filename = "%s" % id
        hash_object = hashlib.md5(filename.encode())

        md5_hash = hash_object.hexdigest()

        filename = md5_hash
        filename = "sched/profile/%s.jpg" % filename

        url_upload = get_upload_presigned_url(filename)
        #url_download = get_download_presigned_url(filename)
        url_download = SPACES_URL + filename

        return Response({'url_upload': url_upload, 'url_download': url_download})


class UserGroupImageView(APIView):
    def get(self, request):
        user = self.request.user
        group_id = self.request.query_params.get("group_id", None)
        if group_id == None or len(group_id) == 0:
            raise ValidationError("Enter Group Id")
        try:
            group = UserGroup.objects.get(id=group_id)
        except UserGroup.DoesNotExist:
            raise ValidationError("Group does not exist")
        if self.request.user != group.group_admin:
            raise PermissionDenied("Permission Denied")
        id = int(group_id)

        filename = "group%s" % id
        hash_object = hashlib.md5(filename.encode())

        md5_hash = hash_object.hexdigest()

        filename = md5_hash
        filename = "sched/group/%s.jpg" % filename

        url_upload = get_upload_presigned_url(filename)
        #url_download = get_download_presigned_url(filename)
        url_download=SPACES_URL+filename

        return Response({'url_upload': url_upload, 'url_download': url_download})


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer



class WebsocketsTicketsView(APIView):
    def get(self,request):
        user=self.request.user
        message = str(datetime.now().timestamp() * 1000) + '_' + str(user.id)
        print(message)
        key = config('KEY')

        fernet = Fernet(key)
        encMessage = fernet.encrypt(message.encode())
        encMessage = encMessage.decode()
        ticket_url=WEBSOCKET_URL+"?token="+encMessage

        return Response({'tickets':encMessage,'url':ticket_url})

