from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from business.models import Business
from note.models import Note
from note.task.models import Task
from user.models import User
from business.service.models import Service


@registry.register_document
class TaskDocument(Document):
    tagged_users = fields.NestedField(properties={
        'username': fields.TextField(),
        'id': fields.IntegerField(),
    })

    class Index:
        # Name of the Elasticsearch index
        name = 'tasks'

        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Task

        fields = [
            'id',
            'title',
            'description',

        ]
        related_models = [User]

    def get_instances_from_related(self, related_instance):

        if isinstance(related_instance, User):
            return related_instance.task_tagged.all()


@registry.register_document
class NoteDocument(Document):
    tagged_users = fields.NestedField(properties={
        'username': fields.TextField(),
        'id': fields.IntegerField(),
    })

    class Index:
        # Name of the Elasticsearch index
        name = 'notes'

        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Note

        fields = [
            'id',
            'title',
            'description',

        ]
        related_models = [User]

    def get_instances_from_related(self, related_instance):

        if isinstance(related_instance, User):
            return related_instance.note_tagged.all()


@registry.register_document
class BusinessDocument(Document):
    class Index:
        # Name of the Elasticsearch index
        name = 'businesses'

        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Business

        fields = [
            'id',
            'name',
            'status',
            'address'

        ]


@registry.register_document
class ServiceDocument(Document):
    class Index:
        # Name of the Elasticsearch index
        name = 'services'

        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Service

        fields = [
            'id',
            'name',
            'status',



        ]

