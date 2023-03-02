from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView

from base.filters import UsersFilter
from base.models import User
from base.serializers import UserSerializer


class ProvidersAPIView(ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_provider=True)
    filter_backends = [DjangoFilterBackend]
    filterset_class = UsersFilter

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        # TODO Use pagination
        response.data = response.data[:5]
        return response


class BuyersAPIView(ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_buyer=True)
    filter_backends = [DjangoFilterBackend]
    filterset_class = UsersFilter

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        # TODO Use pagination
        response.data = response.data[:5]
        return response


class TransitersAPIView(ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_transiter=True)
    filter_backends = [DjangoFilterBackend]
    filterset_class = UsersFilter

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        # TODO Use pagination
        response.data = response.data[:5]
        return response
