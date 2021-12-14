from django.urls import path, include
from rest_framework.routers import SimpleRouter

from search.views import SearchViewSet, SearchBusinessViewSet, SearchServiceViewSet

router = SimpleRouter()
router.register('search_task', SearchViewSet, basename='search_task'),
router.register('business_search', SearchBusinessViewSet, basename='search_business'),
router.register('service_search', SearchServiceViewSet, basename="serach_service"),

# router.register('search2', SearchViewSet, basename='search2'),


urlpatterns = [path('', include(router.urls))]
