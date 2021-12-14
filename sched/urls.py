"""sched URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from user.views import MyTokenObtainPairView,WebsocketsTicketsView

TOKEN_OBTAIN_URL_NAME = 'token_obtain_pair'

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path('xip/', admin.site.urls),

    # register all api urls here
    #path('v1/token/', TokenObtainPairView.as_view(), name=TOKEN_OBTAIN_URL_NAME),
    path('v1/token/', MyTokenObtainPairView.as_view(), name=TOKEN_OBTAIN_URL_NAME),
    path('v1/tickets/', WebsocketsTicketsView.as_view(), name='websocket-token'),
    path('v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('v1/', include('user.urls')),
    path('v1/', include('note.urls')),
    path('v1/', include('business.urls')),
    path('v1/', include('search.urls')),
    path('sentry-debug/', trigger_error),


]
