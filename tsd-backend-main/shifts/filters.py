from django_filters import rest_framework as filters
from .models import Shifts, ShiftTemplates, ShiftTypes


class ShiftFilter(filters.FilterSet):
    user = filters.NumberFilter(field_name='user__id')
    shift_type = filters.NumberFilter(field_name='shift_type__id')
    job_title = filters.CharFilter(lookup_expr='icontains')
    shift_date = filters.DateFilter()

    class Meta:
        model = Shifts
        fields = ['user', 'shift_type', 'job_title', 'shift_date']

class ShiftTemplateFilter(filters.FilterSet):
    class Meta:
        model = ShiftTemplates
        fields = ['code','shift_type','is_fixed_time','is_active','start_time','end_time']

class ShiftTypeFilter(filters.FilterSet):
    class Meta:
        model = ShiftTypes
        fields = ['is_work_shift']