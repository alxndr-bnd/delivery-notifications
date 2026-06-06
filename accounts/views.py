from django.conf import settings
from django.contrib.auth import login
from django.db import transaction
from django.shortcuts import redirect
from django.views.generic import CreateView

from deliveries.models import Shop

from .forms import RegisterForm


class RegisterView(CreateView):
    """Self-service registration: create User + linked Shop, then log in."""

    form_class = RegisterForm
    template_name = "accounts/register.html"

    def form_valid(self, form):
        with transaction.atomic():
            user = form.save()
            Shop.objects.create(owner=user, name=form.cleaned_data["store_name"])
        login(self.request, user)
        return redirect(settings.LOGIN_REDIRECT_URL)
