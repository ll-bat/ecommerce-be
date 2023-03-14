from django.urls import path
from base.views import product_views as views

urlpatterns = [
    path('all/', views.GetAllProductsAPIView.as_view(), name="all_products"),
    path('settings/', views.ProductSettingsAPIView.as_view(), name="product_settings"),

    path('create/', views.ProductAPIView.as_view(), name="create_product"),
    path('<str:pk>/', views.ProductAPIView.as_view(), name="get_update_delete_product"),
]
