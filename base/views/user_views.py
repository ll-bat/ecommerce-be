# Django Import
import rest_framework.generics
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

# Rest Framework Import
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics

# Local Import
from base.models import *
from base.serializers import UserSerializer, UserSerializerWithToken, UserRegistrationSerializer, LoginSerializer, \
    ProductSerializer, UserProfileDetailsSerializer, PostSerializer
from base.utils import normalize_serializer_errors
from django.utils.translation import gettext as _


@api_view(['POST'])
def login(request):
    login_serializer = LoginSerializer(data=request.data)
    if login_serializer.is_valid():
        data = login_serializer.data
        user = authenticate(request, username=data.get('username'), password=data.get('password'))
        if user is not None:
            user_json_data = UserSerializer(user).data
            access_token = user.auth_token.key
            return Response({
                'ok': True,
                'result': {
                    **user_json_data,
                    'token': access_token
                },
                'errors': None
            })
        else:
            return Response({
                'ok': False,
                'errors': {'username': _('Invalid username or password')}
            })

    return Response({
        'ok': False,
        'errors': normalize_serializer_errors(login_serializer.errors)
    })


@api_view(['POST'])
def register_user(request):
    data = request.data
    serializer = UserRegistrationSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'ok': True,
            'result': {
                **serializer.data,
                'token': serializer.instance.auth_token.key
            },
            'errors': None
        })
    else:
        return Response({
            'ok': False,
            'errors': normalize_serializer_errors(serializer.errors)
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


class UserProductsAPIView(rest_framework.generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)


class UserAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileDetailsSerializer
    queryset = User.objects.all()


class UserPostsCreateAPIView(generics.CreateAPIView):
    # TODO explore if we need to do validation for rich editor text
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserPostsAPIView(generics.GenericAPIView):
    # TODO explore if we need to do validation for rich editor text
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    def get(self, request, pk):
        posts = Post.objects.filter(user=pk)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

