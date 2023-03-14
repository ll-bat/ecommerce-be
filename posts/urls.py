from django.urls import path
from . import views

urlpatterns = [
    path('comments/', views.CommentCreateView.as_view(), name="create_comment"),
    path('<str:pk>/comments/', views.CommentView.as_view(), name="get_comments"),
    path('<str:pk>/', views.PostView.as_view(), name="get_post"),
]
