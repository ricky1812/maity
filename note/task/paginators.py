from rest_framework.pagination import PageNumberPagination


class TaskListPaginator(PageNumberPagination):
    page_size = 10
