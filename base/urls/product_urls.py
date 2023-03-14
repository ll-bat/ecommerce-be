from django.urls import path
from base.views import product_views as views

urlpatterns = [
    path('all/', views.GetAllProductsAPIView.as_view(), name="all_products"),
    path('settings/', views.ProductSettingsAPIView.as_view(), name="product_settings"),

    path('<str:pk>/', views.GetProductDetailsAPIVIew.as_view(), name="get_product_details"),
]
