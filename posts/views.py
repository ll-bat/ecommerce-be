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


class CommentView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.order_by('-created_at').all()
    serializer_class = CommentSerializer

    def get_queryset(self):
        return self.queryset.filter(post_id=self.kwargs.get('pk'))

    def post(self, request, *args, **kwargs):
        post_id = kwargs.get('pk')
        if not Post.objects.filter(id=post_id).exists():
            return Response({
                'ok': False,
                'errors': {'non_field_errors': [_('Post does not exist')]}
            })
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            return Response({
                'ok': False,
                'errors': {
                    'non_field_errors': [_("Can't create comment. Try again")],
                }
            })
        serializer.save(user=self.request.user, post_id=self.kwargs.get('pk'))
        return Response({
            'ok': True,
            'result': serializer.data
        })
