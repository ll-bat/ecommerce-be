from django.db import models

from base.models import BaseModel, User


# Create your models here.

class Post(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    content = models.TextField(null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_default_select_related_fields(self):
        return ['user']

    def get_default_prefetch_related_fields(self):
        return []
