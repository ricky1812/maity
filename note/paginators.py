from rest_framework.pagination import PageNumberPagination


class NoteListPaginator(PageNumberPagination):
    page_size = 10
