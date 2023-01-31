from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView

from base.filters import ProvidersFilter
from base.models import User
from base.serializers import UserSerializer


class ProvidersAPIView(ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_provider=True)
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProvidersFilter

