from django.urls import path

from base.views.general_views import ProvidersAPIView, BuyersAPIView

urlpatterns = [
    path('buyers/', BuyersAPIView.as_view(), name="buyers"),
    path('providers/', ProvidersAPIView.as_view(), name="providers"),
]
