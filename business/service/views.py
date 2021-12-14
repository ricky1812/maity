from djmoney.money import Money
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from business.models import Business
from business.service.models import Service, ServiceCategory
from business.service.permissions import IsServiceCreator
from business.service.serializers import ServiceSerializer, ServiceCategorySerialzier, ServiceCategoryListSerialzier
from business.paginators import ServiceListPaginator
from rest_framework.exceptions import PermissionDenied


class ServiceViewSet(mixins.ListModelMixin,

                     viewsets.GenericViewSet):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        business_id = self.request.query_params.get("business_id", None)
        if business_id == None:
            raise ValidationError("Enter Business Id")
        if len(business_id) == 0:
            raise ValidationError("Enter Business Id")
        try:
            business = Business.objects.get(id=business_id)
        except Business.DoesNotExist:
            raise ValidationError("Doesnt Exist")
        service_categories = business.category.service_categories.all()

        if business.created_by != self.request.user:
            return Service.objects.order_by("name").filter(archieved=False).filter(status=0)  # only active business
        status_id = self.request.query_params.get("status_id", None)
        if status_id == None or len(status_id) == 0:
            raise ValidationError("Enter status")
        status_id = int(status_id)
        return Service.objects.order_by("name").filter(archieved=False).filter(status=status_id)


class ServiceDetailViewSet(mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           mixins.CreateModelMixin,
                           mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [IsServiceCreator]

    def get_queryset(self):
        return Service.objects.all()

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
            user = self.request.user
            hashcode = self.request.data.get('hashcode', None)
            business_id = self.request.data.get('business_id', None)
            business = Business.objects.get(id=business_id)

            if business.created_by != user:
                raise PermissionDenied("Permission Denied")
            money = self.request.data.get('money', None)
            currency = self.request.data.get('currency', None)

            cost = Money(money, currency)

            category_id = self.request.data.get('category_id', None)
            category = ServiceCategory.objects.get(id=category_id)

            new_service = serializer.save(business=business, cost=cost, category=category, hashcode=hashcode)
        except Exception as e:
            raise ValidationError(e)

    def perform_update(self, serializer):
        instance = serializer.save()
        try:
            service = Service.objects.get(id=instance.id)
            business = service.business
            user = self.request.user

            category_id = self.request.data.get('category_id', None)

            if category_id != None:
                category = ServiceCategory.objects.get(id=category_id)
                instance.category = category

            money = instance.cost.amount
            currency = instance.cost.currency
            get_money = self.request.data.get('money', None)

            get_currency = self.request.data.get('currency', None)
            if (get_money != None):
                money = get_money
            if (get_currency != None):
                currency = get_currency
            instance.cost = Money(money, currency)

            instance.save()
        except Exception as e:
            raise ValidationError(e)


class ServiceCategoryViewSet(mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    serializer_class = ServiceCategorySerialzier

    def get_serializer_context(self):
        context = super(ServiceCategoryViewSet, self).get_serializer_context()
        context.update({"request": self.request.query_params.get("business_id")})
        return context

    def get_queryset(self):
        business_id = self.request.query_params.get("business_id", None)
        if business_id == None:
            raise ValidationError("Enter Business Id")
        if len(business_id) == 0:
            raise ValidationError("Enter Business Id")
        try:
            business = Business.objects.get(id=business_id)
        except Business.DoesNotExist:
            raise ValidationError("Doesnt Exist")
        service_categories = business.category.service_categories.all()

        return service_categories


class ServiceCategoryListViewSet(mixins.ListModelMixin,
                                 viewsets.GenericViewSet):
    serializer_class = ServiceCategoryListSerialzier
    pagination_class = ServiceListPaginator

    def get_queryset(self):
        return ServiceCategory.objects.all()
