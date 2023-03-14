# Django Import
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, generics

# Rest Framework Import
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.filters import ProductsFilter
from base.models import *
from base.serializers import ProductSerializer, ProductSettingsSerializer
from django.utils.translation import gettext as _

from base.utils import normalize_serializer_errors


# Get all the products with query

class GetAllProductsAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.order_by('-created_at')
    permission_classes = []
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductsFilter

    def get_queryset(self):
        return self.queryset.select_related(
            'user', 'buyer', 'provider', 'transiter',
            'location', 'live_location', 'product_list'
        )


class GetProductAPIView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects
    permission_classes = []

    def get_queryset(self):
        return self.queryset.select_related(
            'user', 'buyer', 'provider', 'transiter',
            'location', 'live_location', 'product_list'
        )

    def retrieve(self, request, *args, **kwargs):
        product = self.get_queryset().filter(_id=self.kwargs.get('pk')).first()
        if not product:
            return Response({
                'ok': False,
                'errors': {
                    'non_field_errors': [_('Product not found')]
                },
            })
        product.seen_count += 1
        product.save()
        return Response({
            'ok': True,
            'result': ProductSerializer(product).data,
        })


class ProductSettingsAPIView(APIView):
    def get(self, request):
        return Response({
            'ok': True,
            'result': ProductSettingsSerializer().to_representation({}),
        })

    # Update single products


class GetProductDetailsAPIVIew(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def get_queryset(self):
        return self.queryset.select_related(
            'user', 'buyer', 'provider', 'transiter',
            'location', 'live_location', 'product_list'
        )

    def get_object(self):
        return self.get_queryset().filter(
            _id=self.kwargs.get('pk'),
        ).first()