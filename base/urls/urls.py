from django.urls import path, include
from base.urls import product_urls, user_urls, order_urls

urlpatterns = [
    path('products/', include(product_urls)),
    path('users/', include(user_urls)),
    path('orders/', include(order_urls)),
]
