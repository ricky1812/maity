from django.apps import AppConfig


class TaskConfig(AppConfig):
    name = 'note.task'

    def ready(self):
        import utility.signals
        import note.task.signals
