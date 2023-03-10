from rest_framework import serializers

from base.serializers import ExpandSerializer
from posts.models import Post


class PostSerializer(ExpandSerializer, serializers.ModelSerializer):
    user_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'user_data')
        fields = ('content',) + read_only_fields
        extra_kwargs = {
            field: {"read_only": True} for field in read_only_fields
        }
