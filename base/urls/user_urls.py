from django.urls import path
from base.views import user_views as views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('', views.getUsers, name="users"),
    path('profile/', views.get_user_profile, name="user_profile"),
    path('profile/update/', views.updateUserProfile, name="user_profile_update"),
    path('login/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('<str:pk>/', views.getUserById, name="get_user"),
    path('update/<str:pk>/', views.updateUser, name="updateUser"),
    path('delete/<str:pk>/', views.delete_user, name="delete_user"),
]
