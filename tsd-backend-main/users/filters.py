from django_filters import rest_framework as filters, Filter
from .models import Users


class MultiValueFilter(Filter):
    def filter(self, qs, value):
        if not value:
            return qs
        values = value.split(',')
        return super().filter(qs, values)

class UserFilter(filters.FilterSet):
    job_title = filters.CharFilter(lookup_expr='icontains')
    team_name = filters.CharFilter(field_name='team_id__team_name', lookup_expr='in')

    class Meta:
        model = Users
        fields = ['is_active']