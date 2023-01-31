from django.urls import path

from base.views.general_views import BuyersAPIView

urlpatterns = [
    path('buyers/', BuyersAPIView.as_view(), name="buyers"),
]
