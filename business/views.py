import hashlib
import json
import sys

import requests
from decouple import config
from django.contrib.gis.db.models.functions import GeometryDistance
from django.contrib.gis.geos import Point
from django.db.models import Q
from geopy.geocoders import Nominatim
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.views import APIView

from business.models import Business, BusinessCategory, BusinessTimeSlot, ProviderDetail
from business.permissions import IsCreator, IsProviderDetail
from business.serializers import (
    BusinessDetailSerializer, BusinessSerializer, SearchBusinessSerializer, BusinessMaskSerializer,
    BusinessCategorySerializer,
    BusinessDatesSerializer, AverageRatingSerializer,
    ProviderDetailSerializer,
)
from business.paginators import BusinessListPaginator
from user.models import UserGroup, User

import datetime as dt
from datetime import date, datetime
from rest_framework.response import Response

from utility.do_spaces import get_upload_presigned_url, get_download_presigned_url

from note.task.views import checkFreeTime

web_hook_url = config('SLACK_URL')

SPACES_URL = 'https://assets.pointapp.in/'


class BusinessViewSet(mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = BusinessSerializer
    pagination_class = BusinessListPaginator

    def get_queryset(self):
        user = self.request.user
        return Business.objects.filter(Q(group__in=user.user_groups.all()) | Q(created_by=user)).distinct()


class BusinessListSet(mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = BusinessSerializer
    pagination_class = BusinessListPaginator

    def get_queryset(self):
        user = self.request.user
        return Business.objects.all()


class BusinessCategoryViewSet(mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    serializer_class = BusinessCategorySerializer
    pagination_class = BusinessListPaginator

    def get_queryset(self):
        return BusinessCategory.objects.all()


class BusinessDetailViewSet(mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            viewsets.GenericViewSet):
    permission_classes = [IsCreator]

    def get_serializer_class(self, *args, **kwargs):

        if self.request.method == 'POST':
            return BusinessDetailSerializer
        params = kwargs
        lookup = self.lookup_url_kwarg or self.lookup_field

        user_pk = self.kwargs[lookup]

        if lookup and lookup in self.kwargs:
            business_pk = self.kwargs[lookup]

            business = Business.objects.get(id=business_pk)

            if business.created_by == self.request.user:
                return BusinessDetailSerializer
            else:
                return BusinessMaskSerializer

    def get_queryset(self):
        user = self.request.user
        return Business.objects.all()

    def perform_create(self, serializer):

        category_id = self.request.data.get('category_id', None)
        if category_id == None:
            raise ValidationError("Enter Category id")
        try:
            category = BusinessCategory.objects.get(id=category_id)
        except BusinessCategory.DoesNotExist:
            raise ValidationError("Category doesnt exist")
        try:
            new_business = serializer.save(created_by=self.request.user, category=category)
        except Exception as e:
            raise ValidationError(e)
        try:
            lat = self.request.data.get('latitude', None)
            long = self.request.data.get('longitude', None)
            if lat != None and long != None:
                location = Point(long, lat, srid=4326)
                new_business.location = location
                new_business.save()
        except Exception as e:
            raise ValidationError(e)

        slack_msg = {
            'text': "A new business has been created with name " + new_business.name + " with id " + str(
                new_business.id)
        }
        requests.post(web_hook_url, data=json.dumps(slack_msg))

        # ...................................................adding timeslots

        business_id = new_business.id

        days = self.request.data.get('day')

        starts = self.request.data.get('start')
        ends = self.request.data.get('end')

        for i in range(0, len(days)):
            day = days[i]
            try:
                s = new_business.timeslots.all().get(day=day)
            except:
                start = starts[i]
                end = ends[i]
                start = float(start)
                end = float(end)
                start = dt.datetime.utcfromtimestamp(start / 1000)
                end = dt.datetime.utcfromtimestamp(end / 1000)

                new_slot = BusinessTimeSlot.objects.create(business=new_business, day=day, start_time=start.time(),
                                                           start_date=start.date(),
                                                           end_time=end.time(), end_date=end.date())
                new_slot.save()

    def perform_update(self, serializer):
        instance = serializer.save()
        group_id = self.request.data.get('group_id', None)
        if group_id != None:

            try:
                group = UserGroup.objects.get(id=group_id)

                if group.group_admin != self.request.user:
                    raise PermissionDenied("Permission Denied")

                instance.group = group
                instance.save()
            except Exception as e:
                raise ValidationError(e)

        business_id = instance.id
        business = Business.objects.get(id=business_id)

        days = self.request.data.get('day', None)

        starts = self.request.data.get('start')
        ends = self.request.data.get('end')
        if days != None:
            t = business.timeslots.all().delete()
            for i in range(0, len(days)):
                day = days[i]
                try:
                    s = business.timeslots.all().get(day=day)
                except:
                    start = starts[i]
                    end = ends[i]
                    start = float(start)
                    end = float(end)
                    start = dt.datetime.utcfromtimestamp(start / 1000)
                    end = dt.datetime.utcfromtimestamp(end / 1000)

                    new_slot = BusinessTimeSlot.objects.create(business=business, day=day, start_time=start.time(),
                                                               start_date=start.date(),
                                                               end_time=end.time(), end_date=end.date())
                    new_slot.save()
        lat = self.request.data.get('latitude', None)
        long = self.request.data.get('longitude', None)
        try:
            if lat != None and long != None:
                location = Point(long, lat, srid=4326)
                instance.location = location
                instance.save()
        except Exception as e:
            raise ValidationError(e)

        slack_msg = {
            'text': "A new business has been updated with name " + instance.name + " with id " + str(
                instance.id)
        }

        # updating timeslots

        requests.post(web_hook_url, data=json.dumps(slack_msg))


class NearbyBusinessViewSet(mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = SearchBusinessSerializer

    def get_queryset(self):
        user = self.request.user
        businesses = Business.objects.all()

        longitude = self.request.query_params.get("longitude", None)
        latitude = self.request.query_params.get("latitude", None)
        if (latitude == None or longitude == None or len(latitude) == 0 or len(longitude) == 0):
            raise ValidationError("Enter Coordinates Properly")
        longitude = float(longitude)  #
        latitude = float(latitude)  #
        user_location = Point(longitude, latitude, srid=4326)

        return businesses.annotate(distance=GeometryDistance('location', user_location)).order_by('distance')


class BusinessDatesViewSet(mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    serializer_class = BusinessDatesSerializer

    def list(self, request):
        business_id = self.request.query_params.get("business_id", None)
        if business_id == None:
            raise ValidationError("Enter Business Id")

        today = date.today()

        business = Business.objects.get(id=business_id)
        timeslot = business.timeslots.all()
        delta = dt.timedelta(days=1)
        count = 7  # Total number of future days
        date_list = []
        while (count > 0):
            day = today.weekday() + 1

            try:
                t = timeslot.get(day=day)

                sd = datetime.combine(today, t.start_time).timestamp() * 1000  # starting date

                fd = datetime.combine(today, t.end_time).timestamp() * 1000  # final date

                block_time = checkFreeTime(business_id, today)

                date_list.append(
                    {"day": day, "start_time": t.start_time, "end_time": t.end_time, "start_date": sd, "end_date": fd,
                     "blocked": block_time})


            except Exception as e:

                pass

            today = today + delta
            count -= 1
        return Response(date_list)


class UserLocationViewSet(mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    def list(self, request):
        user = self.request.user

        longitude = self.request.query_params.get("longitude", None)
        latitude = self.request.query_params.get("latitude", None)
        if (latitude == None or longitude == None or len(latitude) == 0 or len(longitude) == 0):
            raise ValidationError("Enter Coordinates Properly")
        longitude = float(longitude)  #
        latitude = float(latitude)  #
        user_location = Point(latitude, longitude, srid=4326)

        geolocator = Nominatim(user_agent="sched")
        location = geolocator.reverse(user_location, timeout=None)
        if location == None:
            raise ValidationError("Enter coordinates properly")
        address = location.raw['address']

        country = address['country']
        city = address['city']
        state = address['state']
        road = address['road']
        suburb = address['suburb']
        country_code = address['country_code']

        location = []
        location.append({"road": road, "suburb": suburb, "city": city, "state": state, "country": country,
                         "country_code": country_code})
        return Response(location)


class BusinessImageView(APIView):
    def get(self, request):

        business_id = self.request.query_params.get("business_id", None)
        count = self.request.query_params.get("count", 0)
        count = int(count)
        if business_id == None or len(business_id) == 0:
            raise ValidationError("Enter Business Id")
        id = business_id
        try:
            business = Business.objects.get(id=id)
        except Business.DoesNotExist:
            raise ValidationError("Business does not exits")
        if business.created_by != self.request.user:
            raise PermissionDenied("Permission Denied")

        filename = "%s" % id
        filename = filename + "business"
        hash_object = hashlib.md5(filename.encode())

        md5_hash = hash_object.hexdigest()

        filename = md5_hash
        business_name = business.name
        business_name = business_name.replace(' ', '_')

        flag = 1
        name = "sched/business/%s/" % business_name
        urls = []
        while (flag <= count):
            newname = name + "%s" % flag + "%s.jpg" % filename

            flag += 1

            url_upload = get_upload_presigned_url(newname)
            # url_download = get_download_presigned_url(newname)
            url_download = SPACES_URL + newname
            urls.append({'url_upload': url_upload, 'url_download': url_download})
        return Response({'result': urls})


class AverageRatingsViewSet(mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = AverageRatingSerializer

    def get_queryset(self):
        business_id = self.request.query_params.get('business_id', None)
        if business_id == None or len(business_id) == 0:
            raise ValidationError("Enter Business id")
        try:
            business = Business.objects.get(id=business_id)
        except Exception as e:
            raise ValidationError(e)
        return Business.objects.filter(id=business_id)


class ProviderDetailViewSet(mixins.CreateModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = ProviderDetailSerializer
    permission_classes = [IsProviderDetail]

    def get_queryset(self):
        return ProviderDetail.objects.all()

    def retrieve(self, request, *args, **kwargs):

        id = kwargs['pk']

        business_id = self.request.query_params.get('business_id', None)
        if business_id == None:
            raise ValidationError("Enter Business Id")
        user = User.objects.get(id=id)
        business = Business.objects.get(id=business_id)
        detail = ProviderDetail.objects.get(provider=user, business=business)

        return Response(self.get_serializer(detail).data)

    def partial_update(self, request, *args, **kwargs):

        id = kwargs['pk']
        business_id = self.request.data.get('business_id', None)

        try:
            detail = ProviderDetail.objects.get(provider=User.objects.get(id=id),
                                                business=Business.objects.get(id=business_id))
        except Exception as e:
            raise ValidationError(e)

        if detail.business.created_by != self.request.user:
            raise PermissionDenied("You do not have permission")

        try:
            updated_detail = self.get_serializer(detail, data=request.data, partial=True)
        except Exception as e:
            raise ValidationError(e)

        if updated_detail.is_valid():
            updated_detail.save()
        else:
            return Response({"data": "invalid"})

        return Response(updated_detail.data)

    def perform_create(self, serializer):
        user_id = self.request.data.get('user_id', None)
        business_id = self.request.data.get('business_id', None)
        try:
            business = Business.objects.get(id=business_id)
        except Exception as e:
            raise ValidationError(e)

        if business.created_by != self.request.user:
            raise PermissionDenied("You do not have permisision")

        try:
            new_detail = serializer.save(provider=User.objects.get(id=user_id),
                                         business=Business.objects.get(id=business_id))
        except Exception as e:
            raise ValidationError(e)
