from decouple import config

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.authtoken.models import Token
from cryptography.fernet import Fernet

from user.models import User, UserGroup
from utility.helpers import TimestampField
from datetime import datetime


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'display_name', 'username', 'phone_number']


class UserMaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class UserGroupSerializer(serializers.ModelSerializer):
    group_admin = UserSerializer()
    created_at = TimestampField()
    users = UserSerializer(many=True)

    class Meta:
        model = UserGroup
        fields = ['id', 'name', 'image', 'users', 'group_admin', 'created_at']


class UserGroupDetailSerializer(serializers.ModelSerializer):
    group_admin = UserSerializer(read_only=True)
    created_at = TimestampField(read_only=True)
    users = UserSerializer(many=True, read_only=True)

    class Meta:
        model = UserGroup
        fields = ['id', 'name', 'image', 'description', 'users', 'group_admin', 'classification', 'created_at']


class UserMaskGroupSerializer(serializers.ModelSerializer):
    users = UserMaskSerializer(many=True)

    class Meta:
        model = UserGroup
        fields = ['id', 'name', 'image', 'users']


class UserDetailSerializer(serializers.ModelSerializer):
    user_groups = UserGroupDetailSerializer(many=True)
    last_login = TimestampField()

    class Meta:
        model = User
        fields = ['id', 'image_url', 'display_name', 'email', 'visibility', 'username', 'phone_number', 'user_groups',
                  'last_login']
        read_only_fields = ('id', 'username')


# token authentication..

class MyTokenObtainPairSerializer(TokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        if self.user.last_login != None:
            login_time = self.user.last_login.timestamp() * 1000
        else:
            login_time = datetime.now().timestamp() * 1000

        # Add extra responses here
        data['last_login'] = login_time

        new_login_time = datetime.now()
        self.user.last_login = new_login_time
        self.user.save()


        return data


