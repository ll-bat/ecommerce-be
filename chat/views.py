# -*- coding: utf-8 -*-
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
    ListView,
)
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView,
)

from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

from base.models import User
from .models import (
    MessageModel,
    DialogsModel,
    UploadedFile
)
from .serializers import serialize_message_model, serialize_dialog_model, serialize_file_model, UserSerializer
from django.db.models import Q

from django.contrib.auth.mixins import LoginRequiredMixin

from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.core.paginator import Page, Paginator
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.urls import reverse_lazy
from django.forms import ModelForm
import json


class MessagesModelList(ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.kwargs.get('dialog_with'):
            qs = MessageModel.objects \
                .filter(Q(recipient=self.request.user, sender=self.kwargs['dialog_with']) |
                        Q(sender=self.request.user, recipient=self.kwargs['dialog_with'])) \
                .select_related('sender', 'recipient')
        else:
            qs = MessageModel.objects.filter(Q(recipient=self.request.user) |
                                             Q(sender=self.request.user)).prefetch_related('sender', 'recipient',
                                                                                           'file')

        return qs.order_by('-created')

    def get(self, request, *args, **kwargs):
        user_pk = self.request.user.pk
        data = [serialize_message_model(i, user_pk) for i in self.get_queryset()]
        # page: Page = context.pop('page_obj')
        # paginator: Paginator = context.pop('paginator')
        return_data = {
            'page': 0,
            'pages': 0,
            'data': data
        }
        return JsonResponse(return_data)


class DialogsModelList(ListAPIView):
    permission_classes = [IsAuthenticated]

    # paginate_by = getattr(settings, 'DIALOGS_PAGINATION', 20)

    def get_queryset(self):
        qs = DialogsModel.objects.filter(Q(user1_id=self.request.user.pk) | Q(user2_id=self.request.user.pk)) \
            .select_related('user1', 'user2')
        return qs.order_by('-created')

    def get(self, request, *args, **kwargs):
        # TODO: add online status
        user_pk = self.request.user.pk
        queryset = self.get_queryset()
        data = [serialize_dialog_model(i, user_pk) for i in queryset]
        # page: Page = context.pop('page_obj')
        # paginator: Paginator = context.pop('paginator')
        return_data = {
            'page': 0,
            'pages': 0,
            'data': data
        }
        return JsonResponse(return_data)


class SelfInfoView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        data = {
            "username": user.get_username(),
            "pk": str(user.pk)
        }
        return JsonResponse(data)


class UsersAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = User.objects.all()
        data = UserSerializer(queryset, many=True).data
        return JsonResponse(data, safe=False)


# 2.5MB - 2621440
# 5MB - 5242880
# 10MB - 10485760
# 20MB - 20971520
# 50MB - 5242880
# 100MB 104857600
# 250MB - 214958080
# 500MB - 429916160
# MAX_UPLOAD_SIZE = getattr(settings, 'MAX_FILE_UPLOAD_SIZE', 5242880)

class UploadForm(ModelForm):
    # TODO: max file size validation
    # def check_file(self):
    #     content = self.cleaned_data["file"]
    #     content_type = content.content_type.split('/')[0]
    #     if (content._size > MAX_UPLOAD_SIZE):
    #         raise forms.ValidationError(_("Please keep file size under %s. Current file size %s")%(filesizeformat(MAX_UPLOAD_SIZE), filesizeformat(content._size)))
    #     return content
    #
    # def clean(self):

    class Meta:
        model = UploadedFile
        fields = ['file']


class UploadView(LoginRequiredMixin, CreateView):
    http_method_names = ['post', ]
    model = UploadedFile
    form_class = UploadForm

    def form_valid(self, form: UploadForm):
        self.object = UploadedFile.objects.create(uploaded_by=self.request.user, file=form.cleaned_data['file'])
        return JsonResponse(serialize_file_model(self.object))

    def form_invalid(self, form: UploadForm):
        context = self.get_context_data(form=form)
        errors_json: str = context['form'].errors.get_json_data()
        return HttpResponseBadRequest(content=json.dumps({'errors': errors_json}))
