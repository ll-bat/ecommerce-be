from django.shortcuts import render
from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext as _

from base.utils import normalize_serializer_errors
from posts.models import Post, Comment
from posts.serializers import PostSerializer, CommentSerializer


# Create your views here.


class PostView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.all()
    serializer_class = PostSerializer


class CommentCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.order_by('-created_at').all()
    serializer_class = CommentSerializer

    def get_queryset(self):
        return self.queryset.filter(post_id=self.kwargs.get('pk')).select_related('user')
