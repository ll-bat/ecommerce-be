from django.urls import path
from . import views

urlpatterns = [
    path('<str:pk>/comments/', views.CommentView.as_view(), name="get_write_comment"),
    path('<str:pk>/', views.PostView.as_view(), name="get_post"),
]
