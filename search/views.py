# class SearchViewSet(mixins.ListModelMixin,
#                   viewsets.GenericViewSet):
# serializer_class = TaskSerializer

# def get_queryset(self):
# title= self.request.query_params.get('title',None)
# asks=TaskDocument.search().filter("match",title=title)


from elasticsearch_dsl.query import Q
# return Task.objects.all()
from rest_framework import mixins, viewsets

from business.models import Business
from business.serializers import BusinessSerializer
from business.service.serializers import ServiceSerializer
from business.paginators import BusinessListPaginator, ServiceListPaginator
from note.permissions import IsCreator
from note.serializers import NoteListSerializer
from note.task.paginators import TaskListPaginator
from note.task.serializers import TaskListSerializer
from search.documents import TaskDocument, NoteDocument, BusinessDocument, ServiceDocument
from rest_framework.exceptions import ValidationError


class SearchViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    # serializer_class = TaskListSerializer
    pagination_class = TaskListPaginator
    permission_classes = [IsCreator]

    def get_serializer_class(self):
        isTask = self.request.query_params.get("isTask", False)
        if isTask and isTask.lower()=='true':
            return TaskListSerializer
        return NoteListSerializer

    def get_queryset(self):
        ''' return queryset '''

        title = self.request.query_params.get('title', None)
        tagged_users = self.request.query_params.get('tagged_users', None)
        isTask = self.request.query_params.get("isTask", False)
        if isTask:
            isTask = isTask.lower() == 'true'
        if isTask:
            SearchDocument = TaskDocument
        else:
            SearchDocument = NoteDocument

        if title != None:
            if isTask:
                tasks = TaskDocument.search().filter("match_phrase_prefix", title=title)
            else:
                tasks = NoteDocument.search().filter("match_phrase_prefix", title=title)
            user=self.request.user
            groups = user.user_groups.all()
            tasks=tasks.to_queryset()
            q1=tasks.filter(user_groups__in=groups)
            q2=tasks.filter(created_by=user)
            q3=tasks.filter(tagged_users=user)
            q=q1|q2|q3
            q=q.distinct()

            return q
        if tagged_users != None:
            tasks = SearchDocument.search().query("nested", path='tagged_users', query=Q('match_phrase_prefix',
                                                                                         tagged_users__username=tagged_users)).to_queryset()
            return tasks
        else:
            tasks = []
            return tasks


class SearchBusinessViewSet(mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = BusinessSerializer
    pagination_class = BusinessListPaginator

    def get_queryset(self):
        ''' return queryset '''
        name = self.request.query_params.get('name', None)
        if(name==None):
            raise ValidationError("Enter Name")
        SearchDocument = BusinessDocument
        if name != None:
            businesses = BusinessDocument.search().filter("match_phrase_prefix", name=name)
        return businesses.to_queryset()


class SearchServiceViewSet(mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = ServiceSerializer
    pagination_class = ServiceListPaginator

    def get_queryset(self):
        ''' return queryset '''
        name = self.request.query_params.get('name', None)
        if name==None:
            raise ValidationError("Enter Name")




        SearchDocument = ServiceDocument
        if name != None:
            services = ServiceDocument.search().filter("match_phrase_prefix", name=name)

        return services.to_queryset().order_by('name').distinct('name')

