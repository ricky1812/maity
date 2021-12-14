from rest_framework.serializers import ModelSerializer

from utility.models import TimeSlot


def get_timeslot_serializer(model_class, field_list: list = None):
    # send field_list to override fields in Serializer
    if model_class.__bases__[0] == TimeSlot:
        class TimeSlotSerializer(ModelSerializer):
            class Meta:
                model = model_class
                fields = field_list if field_list is not None else ['day', 'start_time', 'end_time', 'start_date',
                                                                    'end_date']
        return TimeSlotSerializer
    else:
        raise Exception('model is not a subclass of utility.models.Timeslot')
