from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.apps import apps

# TODO: Add new apps added to project here for automatic validation
user_apps = list(apps.get_app_config('user').get_models())
business_apps = list(apps.get_app_config('business').get_models())
business_service_apps = list(apps.get_app_config('service').get_models())
note_apps = list(apps.get_app_config('note').get_models())
task_apps = list(apps.get_app_config('task').get_models())

all_apps = user_apps + business_apps + business_service_apps + note_apps + task_apps


@receiver(pre_save)
def pre_save_handler(sender, instance, **kwargs):
    '''Validates all defined models before save()'''
    if type(instance) in all_apps:
        instance.full_clean()
