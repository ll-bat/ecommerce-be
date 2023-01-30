import datetime

import django_filters as filters

from base.models import Product


class ProductsFilter(filters.FilterSet):
    customs_clearance = filters.BooleanFilter(field_name='customs_clearance')
    location = filters.NumberFilter(field_name='location_id')
    live_location = filters.NumberFilter(field_name='live_location_id')
    period = filters.NumberFilter(field_name='period', method='filter_period')
    year_from = filters.NumberFilter(field_name='year', lookup_expr='gte')
    year_to = filters.NumberFilter(field_name='year', lookup_expr='lte')
    price_from = filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_to = filters.NumberFilter(field_name='price', lookup_expr='lte')
    announcement_code = filters.CharFilter(field_name='announcement_code', lookup_expr='icontains')
    search = filters.CharFilter(field_name='name', lookup_expr='icontains')
    category = filters.NumberFilter(field_name='category_id')

    def filter_period(self, queryset, name, value):
        minutes_before = int(value)
        min_datetime = datetime.datetime.now() - datetime.timedelta(minutes=minutes_before)
        return queryset.filter(created_at__gte=min_datetime)