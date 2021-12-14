from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import *

router = SimpleRouter()

router.register('services', ServiceViewSet, basename='services')
router.register('servicecategory', ServiceCategoryViewSet, basename='servicecategory')
router.register('service', ServiceDetailViewSet, basename='servicedetail')
router.register('category_list',ServiceCategoryListViewSet, basename="category-list")

urlpatterns = [path('', include(router.urls))]
