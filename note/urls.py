from django.urls import path, include
from rest_framework.routers import SimpleRouter

from note.views import NoteViewSet, NoteDetailViewSet, CheckListDetailViewSet, RecentViewSet, \
    RecentlyTaggedViewSet, RecentUserViewSet, RecentUserGroupViewSet

router = SimpleRouter()
router.register('notes', NoteViewSet, basename='notes')
router.register('note', NoteDetailViewSet, basename='note')

router.register('checklist', CheckListDetailViewSet, basename='checklist')
router.register('recent', RecentViewSet, basename='recent')
router.register('recent_tagged', RecentlyTaggedViewSet, basename='recent-tagged')
router.register('user_tasks', RecentUserViewSet, basename='recent-user')
router.register('user_group_tasks', RecentUserGroupViewSet, basename='recent-groups')

urlpatterns = [path('', include(router.urls)), path('', include('note.task.urls')),
               ]
