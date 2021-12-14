from django.urls import path, include
from rest_framework.routers import SimpleRouter

from note.task.views import TaskViewSet, TaskDetailViewSet, ServiceProviderViewSet, AppointmentDetailViewSet, \
    FreeTimeViewset, FreeServiceProviderViewSet, RecentAppointmentViewSet, FeedBackTagsViewset, FeedbackViewSet
from . import views

router = SimpleRouter()
router.register('tasks', TaskViewSet, basename='task')
router.register('task', TaskDetailViewSet, basename='task')
router.register('providers', ServiceProviderViewSet, basename='provider')
router.register('appointment', AppointmentDetailViewSet, basename='appointment')
router.register('freetime', FreeTimeViewset, basename='freetime')
router.register('freeprovider', FreeServiceProviderViewSet, basename='free-provider')
router.register('recent_appointment', RecentAppointmentViewSet, basename='recent-appointment')
router.register('feedback_tags', FeedBackTagsViewset, basename='feedback-tags')
router.register('feedback', FeedbackViewSet, basename='feedback')

urlpatterns = [path('', include(router.urls)),
               path('calc/', views.Calculate.as_view(), name="calc"), ]
