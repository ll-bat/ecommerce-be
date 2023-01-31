# Django Import
from django.core import paginator
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, generics

# Rest Framework Import
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from base.filters import ProductsFilter
# Local Import
from base.products import products
from base.models import *
from base.serializers import ProductSerializer, ProductSettingsSerializer
from django.utils.translation import gettext as _

from base.utils import normalize_serializer_errors


# Get all the products with query


def get_products_by_query(request, query):
    # TODO optimize queryset
    products = query.order_by('-_id')

    page = request.query_params.get('page') or 1
    paginator = Paginator(products, 8)

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    page = int(page)

    serializer = ProductSerializer(products, many=True)
    return {'products': serializer.data, 'page': page, 'pages': paginator.num_pages}


# noinspection PyShadowingNames
@api_view(['GET'])
def get_products(request):
    products = Product.objects.filter(user=request.user)
    return Response(get_products_by_query(request, products))


class GetAllProductsAPIView(generics.ListAPIView):
    queryset = Product.objects
    permission_classes = []
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductsFilter

    def get(self, request, *args, **kwargs):
        return Response({
            'ok': True,
            'result': get_products_by_query(request, self.filter_queryset(self.get_queryset()))
        })


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
    serializer = ProductSerializer(product)
    return Response({
        'ok': True,
        'result': serializer.data,
    })


# Create a new Product
@api_view(['POST'])
@permission_classes([IsAdminUser])
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
@permission_classes([IsAdminUser])
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
@permission_classes([IsAdminUser])
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


# Upload Image
@api_view(['POST'])
def upload_image(request):
    data = request.data
    product_id = data['product_id']
    product = Product.objects.get(_id=product_id)
    product.image = request.FILES.get('image')
    product.save()
    return Response("Image was uploaded")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_product_review(request, pk):
    user = request.user
    product = Product.objects.get(_id=pk)
    data = request.data

    # 1 Review already exists
    alreadyExists = product.review_set.filter(user=user).exists()

    if alreadyExists:
        content = {'detail': 'Product already reviewed'}
        return Response(content, status=status.HTTP_400_BAD_REQUEST)

    # 2 No Rating or 0
    elif data['rating'] == 0:
        content = {'detail': 'Please Select a rating'}
        return Response(content, status=status.HTTP_400_BAD_REQUEST)

    # 3 Create review
    else:
        review = Review.objects.create(
            user=user,
            product=product,
            name=user.first_name,
            rating=data['rating'],
            comment=data['comment'],
        )

        reviews = product.review_set.all()
        product.num_reviews = len(reviews)

        total = 0

        for i in reviews:
            total += i.rating
        product.rating = total / len(reviews)
        product.save()

        return Response('Review Added')
