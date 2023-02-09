# Django Import
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, generics

# Rest Framework Import
from rest_framework.decorators import api_view, permission_classes
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


@api_view(['GET'])
def get_top_products(request):
    products = Product.objects.filter(rating__gte=4).order_by('-rating')[0:5]
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


# Get single products
@api_view(['GET'])
def get_product(request, pk):
    product = Product.objects.filter(_id=pk).first()
    if not product:
        return Response({
            'ok': False,
            'errors': {
                'non_field_errors': _("Product doesn't exist")
            }
        })
    product.seen_count += 1
    product.save()
    serializer = ProductSerializer(product)
    return Response({
        'ok': True,
        'result': serializer.data,
    })


# Create a new Product
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_product(request):
    serializer = ProductSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response({
            'ok': False,
            'errors': normalize_serializer_errors(serializer.errors)
        })
    serializer.save(user=request.user)
    return Response({
        'ok': True,
        'result': serializer.data,
    })


class ProductSettingsAPIView(APIView):
    def get(self, request):
        return Response({
            'ok': True,
            'result': ProductSettingsSerializer().to_representation({}),
        })

    # Update single products


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_product(request, pk):
    product = Product.objects.filter(_id=pk, user=request.user).first()
    if not product:
        return Response({
            'ok': False,
            'errors': {
                'non_field_errors': [_('Product not found')]
            },
        })

    serializer = ProductSerializer(data=request.data, instance=product)
    if not serializer.is_valid():
        return Response({
            'ok': False,
            'errors': normalize_serializer_errors(serializer.errors)
        })

    serializer.save()
    return Response({
        'ok': True,
        'result': serializer.data,
        'errors': None,
    })


# Delete a product
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_product(request, pk):
    product = Product.objects.filter(_id=pk, user=request.user).first()
    if not product:
        return Response({
            'ok': False,
            'errors': {
                'non_field_errors': [_('Product not found')]
            },
        })
    product.delete()
    return Response({
        'ok': True,
    })
