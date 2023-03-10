from django.urls import path, include
from base.urls import product_urls, user_urls, general_urls
from posts import urls as post_urls

urlpatterns = [
    path('products/', include(product_urls)),
    path('user/', include(user_urls)),
    path('general/', include(general_urls)),
    path('posts/', include(post_urls))
]
