from django.urls import path
from base.views import user_views as views

urlpatterns = [
    path('', views.UsersAPIView.as_view(), name="users"),
    path('me/', views.UserMeAPIView.as_view(), name="user_me"),
    path('login/', views.login, name='login'),
    path('register/', views.register_user, name='register'),
    path('products/', views.UserProductsAPIView.as_view(), name="user_products"),
    path('posts/', views.UserPostsCreateAPIView.as_view(), name="user_posts"),
    path('posts/<str:pk>/', views.UserPostsAPIView.as_view(), name="user_posts"),
    path('follow/<str:pk>/', views.UserFollowAPIView.as_view(), name="user_follow"),
    path('unfollow/<str:pk>/', views.UserUnfollowAPIView.as_view(), name="user_unfollow"),
    path('recommended/', views.UserRecommendedAPIView.as_view(), name="user_recommended"),
    path('profile/', views.UserProfileUpdateAPIView.as_view(), name="user_profile"),
    path('<str:pk>/', views.UserAPIView.as_view(), name="get_user"),
    path('<str:pk>/following/', views.UserFollowingAPIView.as_view(), name="user_following"),
    path('<str:pk>/followers/', views.UserFollowersAPIView.as_view(), name="user_followers"),
    # it's very important to have this route at the end
    # path('<str:pk>/', views.get_user_by_id, name="get_user"),
]
