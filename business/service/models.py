# Create your models here.
from djmoney.models.fields import MoneyField

from business.models import BusinessCategory, Business
from user.models import *
from utility.models import HashModel


class ServiceCategory(TimestampModel):
    name = models.CharField(max_length=64)
    priority = models.PositiveIntegerField()
    business_category = models.ForeignKey(BusinessCategory, related_name='service_categories', on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Service category"
        verbose_name_plural = "Service categories"
        unique_together = (('priority', 'business_category'),)


class Service(TimestampModel, HashModel):
    class Status(models.IntegerChoices):
        ACTIVE = 0
        INACTIVE = 1

    status = models.IntegerField(choices=Status.choices, default=Status.ACTIVE)
    business = models.ForeignKey(Business, related_name='services', on_delete=models.CASCADE)
    name = models.CharField(max_length=64, blank=False, null=False)
    cost = MoneyField(max_digits=14, decimal_places=2, default_currency=None)
    category = models.ForeignKey(ServiceCategory, related_name='services', on_delete=models.PROTECT)
    duration = models.DurationField(null=True, default=None)
    archieved = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    class Meta:
        unique_together = (('business', 'name'))
