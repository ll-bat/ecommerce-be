from abc import ABC

from django.contrib.auth.hashers import make_password
from django.templatetags.static import static
from django.utils.crypto import get_random_string
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.utils.translation import gettext as _

from backend import settings
from .models import *


class ExpandSerializer(serializers.Serializer):
    @staticmethod
    def get_buyer_data(obj):
        if obj.buyer is None:
            return None
        return UserSerializer(obj.buyer).data

    @staticmethod
    def get_provider_data(obj):
        if obj.provider is None:
            return None
        return UserSerializer(obj.provider).data

    @staticmethod
    def get_transiter_data(obj):
        if obj.transiter is None:
            return None
        return UserSerializer(obj.transiter).data

    @staticmethod
    def get_product_list_data(obj):
        if obj.product_list is None:
            return None
        return ProductListSerializer(obj.product_list).data

    @staticmethod
    def get_location_data(obj):
        if obj.location is None:
            return None
        return LocationSerializer(obj.location).data

    @staticmethod
    def get_live_location_data(obj):
        if obj.live_location is None:
            return None
        return LocationSerializer(obj.live_location).data

    @staticmethod
    def get_user_data(obj):
        return UserSerializer(obj.user).data


class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_provider', 'is_buyer',
                  'is_transiter', 'about', 'location']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'is_provider', 'is_buyer', 'is_transiter', 'about', 'location']


class UserProfileDetailsSerializer(serializers.ModelSerializer):
    is_followed_by_me = serializers.SerializerMethodField(read_only=True)
    followers_count = serializers.SerializerMethodField(read_only=True)
    following_count = serializers.SerializerMethodField(read_only=True)

    def get_is_followed_by_me(self, obj):
        return UserFollowers.objects.filter(follower=self.context['request'].user, user=obj).exists()

    def get_followers_count(self, obj):
        return User.objects.filter(followed__user=obj).count()

    def get_following_count(self, obj):
        return User.objects.filter(followers__follower=obj).count()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'is_provider', 'is_buyer', 'is_transiter', 'date_joined', 'is_followed_by_me',
                  'about', 'location', 'followers_count', 'following_count']


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    name = serializers.CharField(source='first_name', max_length=150)
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_username(self, username):
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(_("Username already exists"))
        return username

    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(_("Email already exists"))
        return email

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        user = User.objects.create(**validated_data)
        Token.objects.create(user=user)
        return user

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'name', 'is_buyer', 'is_provider', 'is_transiter']


class ProductSerializer(ExpandSerializer, serializers.ModelSerializer):
    image = serializers.SerializerMethodField(read_only=True)
    product_list = serializers.PrimaryKeyRelatedField(queryset=ProductList.objects.all())
    buyer = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                               queryset=User.objects.filter(is_buyer=True).all())
    provider = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                                  queryset=User.objects.filter(is_provider=True).all())
    transiter = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                                   queryset=User.objects.filter(is_transiter=True).all())
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    live_location = serializers.PrimaryKeyRelatedField(queryset=LiveLocation.objects.all())

    buyer_data = serializers.SerializerMethodField(read_only=True)
    provider_data = serializers.SerializerMethodField(read_only=True)
    transiter_data = serializers.SerializerMethodField(read_only=True)
    product_list_data = serializers.SerializerMethodField(read_only=True)
    user_data = serializers.SerializerMethodField(read_only=True)
    location_data = serializers.SerializerMethodField(read_only=True)
    live_location_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        read_only_fields = ("_id", "user", "image",
                            "rating", "buyer_data", "provider_data", "transiter_data",
                            "product_list_data", "announcement_code", "location_data",
                            "user_data", "created_at", "live_location_data", "seen_count")
        fields = \
            (
                "name", "category", "product_list", "buyer", "provider", "transiter",
                "year", "price", "location", "live_location", "customs_clearance",
                "description"
            ) + read_only_fields
        extra_kwargs = {
            field: {"read_only": True} for field in read_only_fields
        }

    def create(self, validated_data):
        validated_data["announcement_code"] = "AC" + get_random_string(12, "0123456789")
        return super().create(validated_data)

    def get_image(self, obj: Product):
        return settings.DOMAIN_URL + static(obj.image)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ('id', 'name')


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'name')


class LiveLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveLocation
        fields = ('id', 'name')


class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductList
        fields = ('id', 'name')


class ProductSettingsSerializer(serializers.Serializer):
    categories = serializers.SerializerMethodField(read_only=True)
    locations = serializers.SerializerMethodField(read_only=True)
    live_locations = serializers.SerializerMethodField(read_only=True)
    product_list = serializers.SerializerMethodField(read_only=True)

    def get_categories(self, obj):
        categories = ProductCategory.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return serializer.data

    def get_locations(self, obj):
        categories = Location.objects.all()
        serializer = LocationSerializer(categories, many=True)
        return serializer.data

    def get_live_locations(self, obj):
        categories = LiveLocation.objects.all()
        serializer = LiveLocationSerializer(categories, many=True)
        return serializer.data

    def get_product_list(self, obj):
        product_list = ProductList.objects.all()
        serializer = ProductListSerializer(product_list, many=True)
        return serializer.data


class PostSerializer(ExpandSerializer, serializers.ModelSerializer):
    user_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'user_data')
        fields = ('content',) + read_only_fields
        extra_kwargs = {
            field: {"read_only": True} for field in read_only_fields
        }
