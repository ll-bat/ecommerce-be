import django_filters as filters
from django.db.models import Q


class UsersFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name='id')
    query = filters.CharFilter(method='filter_query')

    def filter_query(self, queryset, name, value):
        return queryset.filter(
            Q(email__icontains=value)
            | Q(name__icontains=value)
        )
