from business.serializers import *
from business.service.models import *


class ServiceCategorySerialzier(ModelSerializer):
    business_category = BusinessCategorySerializer()
    services = SerializerMethodField()

    def get_services(self, obj):
        business_id = self.context.get("request")
        business = Business.objects.get(id=business_id)
        all_service = obj.services.all().filter(business=business)

        return ServiceSerializer(all_service, many=True).data

    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'priority', 'business_category', 'services']


class ServiceCategoryListSerialzier(ModelSerializer):
    business_category = BusinessCategorySerializer()

    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'priority', 'business_category']


class ServiceSerializer(ModelSerializer):
    category = ServiceCategoryListSerialzier(read_only=True)
    business = BusinessSerializer(read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'name', 'status', 'cost', 'cost_currency', 'duration', 'archieved', 'category', 'business',
                  'hashcode']
