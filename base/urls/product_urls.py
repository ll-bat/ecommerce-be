from django.urls import path
from base.views import product_views as views

urlpatterns = [
    path('all/', views.GetAllProductsAPIView.as_view(), name="all_products"),

    path('create/', views.create_product, name="create_product"),
    path('settings/', views.ProductSettingsAPIView.as_view(), name="product_settings"),

    path('top/', views.get_top_products, name="top-products"),
    path('<str:pk>/', views.get_product, name="product"),

    path('update/<str:pk>/', views.update_product, name="update_product"),
    path('delete/<str:pk>/', views.delete_product, name="delete_product"),
]
