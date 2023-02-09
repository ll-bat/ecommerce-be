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


class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_provider', 'is_buyer']


class UserSerializerWithToken(UserSerializer):
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'token']

    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    name = serializers.CharField(source='first_name', max_length=150)
    password = serializers.CharField(min_length=8)

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
        fields = ['username', 'email', 'password', 'name', 'is_buyer', 'is_provider']


class ProductSerializer(serializers.ModelSerializer):
    reviews = serializers.SerializerMethodField(read_only=True)
    image = serializers.SerializerMethodField(read_only=True)
    product_list = serializers.PrimaryKeyRelatedField(queryset=ProductList.objects.all())
    buyer = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                               queryset=User.objects.filter(is_buyer=True).all())
    provider = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                                  queryset=User.objects.filter(is_provider=True).all())
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    live_location = serializers.PrimaryKeyRelatedField(queryset=LiveLocation.objects.all())

    buyer_data = serializers.SerializerMethodField(read_only=True)
    provider_data = serializers.SerializerMethodField(read_only=True)
    product_list_data = serializers.SerializerMethodField(read_only=True)
    user_data = serializers.SerializerMethodField(read_only=True)
    location_data = serializers.SerializerMethodField(read_only=True)
    live_location_data = serializers.SerializerMethodField(read_only=True)

    def get_buyer_data(self, obj):
        if obj.buyer is None:
            return None
        return UserSerializer(obj.buyer).data

    def get_provider_data(self, obj):
        if obj.provider is None:
            return None
        return UserSerializer(obj.provider).data

    def get_product_list_data(self, obj):
        if obj.product_list is None:
            return None
        return ProductListSerializer(obj.product_list).data

    def get_location_data(self, obj):
        if obj.location is None:
            return None
        return LocationSerializer(obj.location).data

    def get_live_location_data(self, obj):
        if obj.live_location is None:
            return None
        return LocationSerializer(obj.live_location).data

    def get_user_data(self, obj):
        return UserSerializer(obj.user).data

    class Meta:
        model = Product
        read_only_fields = ("_id", "user", "reviews", "image", "num_reviews",
                            "rating", "buyer_data", "provider_data", "product_list_data",
                            "announcement_code", "location_data", "user_data",
                            "created_at", "live_location_data", "seen_count",)
        fields = \
            (
                "name", "category", "product_list", "buyer", "provider", "year", "price",
                "location", "live_location", "customs_clearance",
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

    def get_reviews(self, obj):
        return []


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
