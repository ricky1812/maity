from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from django.contrib.gis.db import models as geomodels

# Register your models here.
from business.models import Business, BusinessCategory, BusinessTimeSlot, ProviderDetail
from note.task.models import Task
from utility.widgets import LatLongWidget


@admin.register(Task)
class TaskAdmin(OSMGeoAdmin):
    list_display = ('title', 'services', 'description', 'created_by')
    search_fields = ['title']
    ordering = ['-updated_at']

    def services(self, obj):
        return ", ".join([p.name for p in obj.business_services.all()])

    formfield_overrides = {geomodels.PointField: {'widget': LatLongWidget}}


@admin.register(BusinessCategory)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ['name']


@admin.register(Business)
class BusinessAdmin(OSMGeoAdmin):
    list_display = ('name', 'category', 'status', 'location')
    search_fields = ['name']
    ordering = ['name']
    formfield_overrides = {geomodels.PointField: {'widget': LatLongWidget}}


@admin.register(BusinessTimeSlot)
class BusinessTimeSlotAdmin(admin.ModelAdmin):
    list_display = ('day', 'start_time', 'start_date', 'end_time', 'end_date', 'business')


@admin.register(ProviderDetail)
class ProviderDetailAdmin(admin.ModelAdmin):
    list_display = ('provider', 'business')
