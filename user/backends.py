from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import ObjectDoesNotExist
from django.urls import resolve
from firebase_admin.auth import UserNotFoundError, get_user_by_phone_number

from sched.urls import TOKEN_OBTAIN_URL_NAME
from .models import User


class PhoneNumberBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        # Authenticating only when TOKEN_OBTAIN_URL is called
        if resolve(request.path_info).url_name != TOKEN_OBTAIN_URL_NAME:
            return None

        google_user = None
        user = None
        try:
            google_user = get_user_by_phone_number(username)
            user = User.objects.get(phone_number=username)
        except UserNotFoundError:
            return None
        except ObjectDoesNotExist:
            # means google_user exists but not in our DB. We create a new user if password matches google_user's uid
            if google_user.uid == password:
                user = User(username=username, phone_number=username)
                password = User.objects.make_random_password()
                user.set_password(password)
                user.save()
                return user
            else:
                return None
        return user if google_user.uid == password else None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            return None
