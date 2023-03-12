from rest_framework import serializers

from base.serializers import ExpandSerializer
from posts.models import Post, Comment


class PostSerializer(ExpandSerializer, serializers.ModelSerializer):
    user_data = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.SerializerMethodField(read_only=True)

    def get_comments_count(self, obj):
        return obj.comments.count()

    class Meta:
        model = Post
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'user_data', 'comments_count')
        fields = ('content',) + read_only_fields
        extra_kwargs = {
            field: {"read_only": True} for field in read_only_fields
        }


class CommentSerializer(ExpandSerializer, serializers.ModelSerializer):
    user_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        read_only_fields = ('id', 'post', 'user', 'created_at', 'updated_at', 'user_data')
        fields = ('content',) + read_only_fields
        extra_kwargs = {
            field: {"read_only": True} for field in read_only_fields
        }
