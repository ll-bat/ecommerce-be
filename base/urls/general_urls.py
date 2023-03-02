from django.urls import path

from base.views.general_views import ProvidersAPIView, BuyersAPIView, TransitersAPIView

urlpatterns = [
    path('buyers/', BuyersAPIView.as_view(), name="buyers"),
    path('providers/', ProvidersAPIView.as_view(), name="providers"),
    path('transiters/', TransitersAPIView.as_view(), name="transiters"),
]
