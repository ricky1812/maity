from rest_framework.pagination import PageNumberPagination


class BusinessListPaginator(PageNumberPagination):
    page_size = 10

class ServiceListPaginator(PageNumberPagination):
    page_size = 10

