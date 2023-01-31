import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.fields import BLANK_CHOICE_DASH


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


class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, null=False, blank=False, default="name")
    image = models.ImageField(null=True, blank=True, default="/images/placeholder.png", upload_to="images/")
    description = models.TextField(null=False, blank=False, default="description")
    rating = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    num_reviews = models.IntegerField(null=True, blank=True, default=0)

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="buyer_products")
    provider = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="provider_products")
    # category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, null=True, blank=True, default=None)
    category = models.CharField(max_length=512, null=False, blank=False, default="category")
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=False, blank=False)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True, default=None)
    live_location = models.ForeignKey(LiveLocation, on_delete=models.CASCADE, null=True, blank=True, default=None)
    announcement_code = models.CharField(null=False, blank=False, max_length=64)
    customs_clearance = models.BooleanField(null=False, blank=False, default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    _id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return self.name + " | " + str(self.price)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True, default=0)
    comment = models.TextField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    _id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return str(self.rating)


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    paymentMethod = models.CharField(max_length=200, null=True, blank=True)
    taxPrice = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    shippingPrice = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    totalPrice = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    isPaid = models.BooleanField(default=False)
    paidAt = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    isDeliver = models.BooleanField(default=False)
    deliveredAt = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    _id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return str(self.createdAt)


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    qty = models.IntegerField(null=True, blank=True, default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    image = models.CharField(max_length=200, null=True, blank=True)
    _id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return str(self.name)


class ShippingAddress(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=200, null=True, blank=True)
    postalCode = models.CharField(max_length=200, null=True, blank=True)
    country = models.CharField(max_length=200, null=True, blank=True)
    shippingPrice = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    _id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return str(self.address)
