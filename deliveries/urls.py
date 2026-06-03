from django.urls import path

from .views import DeliveryListView

app_name = "deliveries"

urlpatterns = [
    path("", DeliveryListView.as_view(), name="list"),
]
