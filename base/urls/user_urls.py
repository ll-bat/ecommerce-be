from django.urls import path
from base.views import user_views as views

urlpatterns = [
    path('', views.get_users, name="users"),
    path('profile/', views.get_user_profile, name="user_profile"),
    path('login/', views.login, name='login'),
    path('register/', views.register_user, name='register'),
    path('products/', views.UserProductsAPIView.as_view(), name="user_products"),
    # it's very important to have this route at the end
    # path('<str:pk>/', views.get_user_by_id, name="get_user"),
]
