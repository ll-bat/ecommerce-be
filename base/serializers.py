from django.contrib.auth.hashers import make_password
from django.db.models import fields
from django.templatetags.static import static
from django.utils.crypto import get_random_string
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.utils.translation import gettext as _

from backend import settings
from .models import *


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    _id = serializers.SerializerMethodField(read_only=True)
    isAdmin = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', '_id', 'username', 'email', 'name', 'isAdmin', 'is_provider', 'is_buyer']

    def get__id(self, obj):
        return obj.id

    def get_isAdmin(self, obj):
        return obj.is_staff

    def get_name(self, obj):
        name = obj.first_name
        if name == "":
            name = obj.email
        return name


class UserSerializerWithToken(UserSerializer):
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', '_id', 'username', 'email', 'name', 'isAdmin', 'token']

    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    name = serializers.CharField(source='first_name', max_length=150)
    password = serializers.CharField(min_length=8)

    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(_("Email already exists"))
        return email

    def create(self, validated_data):
        return User.objects.create(
            first_name=validated_data['first_name'],
            email=validated_data['email'],
            username=validated_data['email'],
            password=make_password(validated_data['password']),
            is_buyer=validated_data['is_buyer'],
            is_provider=validated_data['is_provider'],
            is_staff=True
        )

    class Meta:
        model = User
        fields = ['email', 'password', 'name', 'is_buyer', 'is_provider']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ()


class ProductSerializer(serializers.ModelSerializer):
    reviews = serializers.SerializerMethodField(read_only=True)
    image = serializers.SerializerMethodField(read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=ProductCategory.objects.all())
    buyer = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                               queryset=User.objects.filter(is_buyer=True).all())
    provider = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                                  queryset=User.objects.filter(is_provider=True).all())
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    live_location = serializers.PrimaryKeyRelatedField(queryset=LiveLocation.objects.all())

    category_data = serializers.SerializerMethodField(read_only=True)
    buyer_data = serializers.SerializerMethodField(read_only=True)
    provider_data = serializers.SerializerMethodField(read_only=True)

    def get_category_data(self, obj):
        if obj.category is None:
            return None
        return CategorySerializer(obj.category).data

    def get_buyer_data(self, obj):
        if obj.buyer is None:
            return None
        return UserSerializer(obj.buyer).data

    def get_provider_data(self, obj):
        if obj.provider is None:
            return None
        return UserSerializer(obj.provider).data

    class Meta:
        model = Product
        read_only_fields = ("_id", "user", "reviews", "image", "num_reviews",
                            "rating", "category_data", "buyer_data", "provider_data",
                            "announcement_code", )
        fields = \
            (
                "name", "category", "buyer", "provider", "year", "price",
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


class ProductSettingsSerializer(serializers.Serializer):
    categories = serializers.SerializerMethodField(read_only=True)
    locations = serializers.SerializerMethodField(read_only=True)
    live_locations = serializers.SerializerMethodField(read_only=True)

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


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    orderItems = serializers.SerializerMethodField(read_only=True)
    shippingAddress = serializers.SerializerMethodField(read_only=True)
    User = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = '__all__'

    def get_orderItems(self, obj):
        items = obj.orderitem_set.all()
        serializer = OrderItemSerializer(items, many=True)
        return serializer.data

    def get_shippingAddress(self, obj):
        try:
            address = ShippingAddressSerializer(obj.shippingaddress, many=False).data
        except:
            address = False663
        return address

    def get_User(self, obj):
        items = obj.user
        serializer = UserSerializer(items, many=False)
        return serializer.data
