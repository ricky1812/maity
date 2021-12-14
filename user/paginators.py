from rest_framework.pagination import PageNumberPagination


class UserListPaginator(PageNumberPagination):
    page_size = 10