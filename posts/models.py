from django.db import models

from base.models import BaseModel, User, TimestampFields


# Create your models here.

class Post(TimestampFields, BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    content = models.TextField(null=False, blank=False)

    def get_default_select_related_fields(self):
        return ['user', 'comments']

    def get_default_prefetch_related_fields(self):
        return []


class Comment(TimestampFields, BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=False, blank=False,
                             related_name='comments')
    content = models.TextField(null=False, blank=False)

    def get_default_select_related_fields(self):
        return ['user']

    def get_default_prefetch_related_fields(self):
        return []
