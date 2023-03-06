import uuid
from abc import abstractmethod

from django.db import models
from django.contrib.auth.models import AbstractUser


class BaseModel(models.Model):
    class Meta:
        abstract = True

    @abstractmethod
    def get_default_select_related_fields(self):
        raise NotImplementedError

    @abstractmethod
    def get_default_prefetch_related_fields(self):
        raise NotImplementedError

    @property
    def objects(self):
        objects = super().objects
        return objects \
            .select_related(*self.get_default_select_related_fields()) \
            .prefetch_related(*self.get_default_prefetch_related_fields())


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None

    name = models.CharField(null=False, blank=False, default='name', max_length=512)
    email = models.EmailField(null=False, blank=False, unique=True)
    id_number = models.CharField(null=True, blank=True, default=None,
                                 max_length=52, unique=True)

    is_provider = models.BooleanField(default=False)
    is_buyer = models.BooleanField(default=False)
    is_transiter = models.BooleanField(default=False)

    about = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        db_table = "users"

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


# Create your models here.

class Provider(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False, unique=True)
    something = models.CharField(max_length=200, null=False, blank=False, unique=True)


class ProductCategory(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Location(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LiveLocation(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProductList(models.Model):
    name = models.CharField(max_length=512, null=False, blank=False, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Product(BaseModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, null=False, blank=False, default="name")
    image = models.ImageField(null=True, blank=True, default="/images/placeholder.png", upload_to="images/")
    description = models.TextField(null=False, blank=False, default="description")
    rating = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="buyer_products")
    provider = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="provider_products")
    transiter = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                                  related_name="transiter_products")
    # category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, null=True, blank=True, default=None)
    product_list = models.ForeignKey(ProductList, on_delete=models.CASCADE, null=True, blank=True, default=None)
    category = models.CharField(max_length=512, null=False, blank=False, default="category")
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=False, blank=False)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True, default=None)
    live_location = models.ForeignKey(LiveLocation, on_delete=models.CASCADE, null=True, blank=True, default=None)
    announcement_code = models.CharField(null=False, blank=False, max_length=64)
    customs_clearance = models.BooleanField(null=False, blank=False, default=True)

    seen_count = models.IntegerField(null=False, blank=False, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    _id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return self.name + " | " + str(self.price)


class BaseModel(models.Model):
    class Meta:
        abstract = True

    @abstractmethod
    def get_default_select_related_fields(self):
        # TODO test this
        return ['buyer', 'provider', 'transiter', 'product_list',
                'location', 'live_location']

    def get_default_prefetch_related_fields(self):
        return []


class Post(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    content = models.TextField(null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_default_select_related_fields(self):
        return ['user']

    def get_default_prefetch_related_fields(self):
        return []


class UserFollowers(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, related_name="followers")
    follower = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, related_name="followed")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_default_select_related_fields(self):
        return []

    def get_default_prefetch_related_fields(self):
        return []
