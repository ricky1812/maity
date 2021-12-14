from django.urls import path, include
from rest_framework.routers import SimpleRouter

from user.views import (
    UserGroupViewSet, UserViewSet, UserGroupDetailViewSet, UserExitViewSet,
    UserCommonGroupViewSet, UserDetailViewSet, UserImageView, UserGroupImageView, MyCreatedUserGroupViewSet
)

router = SimpleRouter()
router.register('user/group', UserGroupDetailViewSet, basename='user_group')
router.register('user/groups', UserGroupViewSet, basename='user-groups')
router.register('user/groups/leavegroup', UserExitViewSet, basename='user-exit')
router.register('user', UserViewSet, basename='user')
router.register('user_detail', UserDetailViewSet, basename='user-detail')
router.register('groups', UserCommonGroupViewSet, basename='commonuser-groups')
router.register('created_groups', MyCreatedUserGroupViewSet, basename='created-groups')

urlpatterns = [
    path('user/upload/', UserImageView.as_view(), name='user-image'),
    path('user_group/upload/', UserGroupImageView.as_view(), name='usergroup-image'),

]

urlpatterns += router.urls
