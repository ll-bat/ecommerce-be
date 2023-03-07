# Django Import
import rest_framework.generics
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend

# Rest Framework Import
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.views import APIView

# Local Import
from base.models import *
from base.serializers import UserSerializer, UserRegistrationSerializer, LoginSerializer, \
    ProductSerializer, UserProfileDetailsSerializer, PostSerializer, UserProfileUpdateSerializer
from base.utils import normalize_serializer_errors
from django.utils.translation import gettext as _

from base.filters import UsersFilter


@api_view(['POST'])
def login(request):
    login_serializer = LoginSerializer(data=request.data)
    if login_serializer.is_valid():
        data = login_serializer.data
        user = authenticate(request, username=data.get('email'), password=data.get('password'))
        if user is not None:
            user_json_data = UserSerializer(user).data
            access_token = user.auth_token.key
            return Response({
                'ok': True,
                'result': {
                    'user_data': user_json_data,
                    'access_token': access_token
                },
                'errors': None
            })
        else:
            return Response({
                'ok': False,
                'errors': {'email': _('Invalid email or password')}
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
                'user_data': serializer.data,
                'access_token': serializer.instance.auth_token.key
            },
            'errors': None
        })
    else:
        return Response({
            'ok': False,
            'errors': normalize_serializer_errors(serializer.errors)
        })


class UsersAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = UsersFilter

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response.data = response.data[:5]
        return response


class UserMeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_json_data = UserSerializer(request.user).data
        access_token = request.user.auth_token.key
        return Response({
            'ok': True,
            'result': {
                'user_data': user_json_data,
                'access_token': access_token
            },
            'errors': None
        })


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
        posts = Post.objects.filter(user=pk).order_by('-created_at')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


class UserFollowAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if str(pk) == str(request.user.id):
            return Response({
                'ok': False,
                'errors': {
                    'non_field_errors': [_('You cannot follow yourself')]
                }
            })
        if UserFollowers.objects.filter(user_id=pk, follower=request.user).exists():
            return Response({
                'ok': False,
                'errors': {
                    'non_field_errors': [_('You are already following this user')]
                }
            })

        UserFollowers.objects.create(user_id=pk, follower=request.user)
        return Response()


class UserUnfollowAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        UserFollowers.objects.filter(user_id=pk, follower=request.user).delete()
        return Response()


class UserProfileUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=False):
            serializer.save()
            return Response({
                'ok': True,
                'result': UserSerializer(user).data,
                'errors': normalize_serializer_errors(serializer.errors),
            })
        return Response({
            'ok': False,
            'result': None,
            'errors': normalize_serializer_errors(serializer.errors),
        })


class UserFollowingAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(followers__follower=self.request.user)


class UserFollowersAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(followed__user=self.request.user)


class UserRecommendedAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.exclude(followers__follower=self.request.user) \
            .exclude(id=self.request.user.id) \
            .exclude(is_superuser=True)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response.data = response.data[:5]
        return response
