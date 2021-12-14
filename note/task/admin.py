from django.contrib import admin

from note.task.models import SubTasks, Feedback, FeedbackTags


# Register your models here.


@admin.register(SubTasks)
class SubTasksAdmin(admin.ModelAdmin):
    list_display = ('task', 'provider')


@admin.register(FeedbackTags)
class FeedbackTagsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('provider', 'business', 'ratings', 'user')
