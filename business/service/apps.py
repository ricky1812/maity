from django.apps import AppConfig


class ServiceConfig(AppConfig):
    name = 'business.service'

    def ready(self):
        pass
