from django.urls import path, include
from rest_framework.routers import SimpleRouter

from business.views import BusinessViewSet, NearbyBusinessViewSet, BusinessDetailViewSet, BusinessDatesViewSet, \
    BusinessListSet, BusinessCategoryViewSet, UserLocationViewSet, BusinessImageView, \
    AverageRatingsViewSet, ProviderDetailViewSet

router = SimpleRouter()
router.register('businesses', BusinessViewSet, basename='businesses')
router.register('business', BusinessDetailViewSet, basename='business')
router.register('business_list', BusinessListSet, basename="business-list")
router.register('search_business', NearbyBusinessViewSet, basename='business-search')
router.register('business_dates', BusinessDatesViewSet, basename='business-dates')
router.register('business_category', BusinessCategoryViewSet, basename='business-category')
router.register('user_location', UserLocationViewSet, basename="user-location")
router.register('ratings', AverageRatingsViewSet, basename='average-ratings')
router.register('provider_detail', ProviderDetailViewSet, basename='provider-detail')

urlpatterns = [path('', include(router.urls)),
               path('business/upload', BusinessImageView.as_view(), name='business-image'),
               path('', include('business.service.urls'))]
