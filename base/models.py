import uuid
from abc import abstractmethod

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    is_provider = models.BooleanField(default=False)
    is_buyer = models.BooleanField(default=False)

    class Meta:
        db_table = "users"


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


class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, null=False, blank=False, default="name")
    image = models.ImageField(null=True, blank=True, default="/images/placeholder.png", upload_to="images/")
    description = models.TextField(null=False, blank=False, default="description")
    rating = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    num_reviews = models.IntegerField(null=True, blank=True, default=0)

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="buyer_products")
    provider = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="provider_products")
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


class Post(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    content = models.TextField(null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_default_select_related_fields(self):
        return ['user']

    def get_default_prefetch_related_fields(self):
        return []
