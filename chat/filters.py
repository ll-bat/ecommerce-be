import django_filters as filters
from django.db.models import Q


class UsersFilter(filters.FilterSet):
    query = filters.CharFilter(method='filter_query')

    def filter_query(self, queryset, name, value):
        return queryset.filter(
            Q(email__icontains=value)
            | Q(username__icontains=value)
            | Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
        )
