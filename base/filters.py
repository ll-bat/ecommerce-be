import datetime

import django_filters as filters
from django.db.models import Q

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
    category = filters.CharFilter(field_name='category', lookup_expr='icontains')
    buyer = filters.NumberFilter(field_name='buyer_id')
    provider = filters.NumberFilter(field_name='provider_id')
    product = filters.NumberFilter(field_name='product_list_id')
    user = filters.NumberFilter(field_name='user_id')

    def filter_period(self, queryset, name, value):
        minutes_before = int(value)
        min_datetime = datetime.datetime.now() - datetime.timedelta(minutes=minutes_before)
        return queryset.filter(created_at__gte=min_datetime)


class BuyersFilter(filters.FilterSet):
    search = filters.CharFilter(field_name='email', lookup_expr='icontains')


class ProvidersFilter(filters.FilterSet):
    search = filters.CharFilter(field_name='email', lookup_expr='icontains')


class UsersFilter(filters.FilterSet):
    query = filters.CharFilter(method='filter_query')

    def filter_query(self, queryset, name, value):
        return queryset.filter(
            Q(email__icontains=value)
            | Q(username__icontains=value)
            | Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
        )
