from django.urls import path

from .views import (
    ApiDocsView,
    DeletedDeliveriesView,
    DeliveryCreateView,
    DeliveryDeleteView,
    DeliveryFeedView,
    DeliveryListView,
    DeliveryMarkDeliveredView,
    DeliveryResendView,
    DeliveryRestoreView,
    DeliveryStartView,
    RecipientLookupView,
    ShopProfileView,
    ToggleCompletedView,
)

app_name = "deliveries"

urlpatterns = [
    path("", DeliveryListView.as_view(), name="list"),
    path("dostava/nova/", DeliveryCreateView.as_view(), name="create"),
    path("klijent/", RecipientLookupView.as_view(), name="recipient_lookup"),
    path("feed/", DeliveryFeedView.as_view(), name="feed"),
    path("obrisane/", DeletedDeliveriesView.as_view(), name="deleted"),
    path("api/", ApiDocsView.as_view(), name="api_docs"),
    path("zavrseno/toggle/", ToggleCompletedView.as_view(), name="toggle_completed"),
    path("dostava/<int:pk>/start/", DeliveryStartView.as_view(), name="start"),
    path("dostava/<int:pk>/obrisi/", DeliveryDeleteView.as_view(), name="delete"),
    path("dostava/<int:pk>/vrati/", DeliveryRestoreView.as_view(), name="restore"),
    path("dostava/<int:pk>/posalji-ponovo/", DeliveryResendView.as_view(), name="resend"),
    path(
        "dostava/<int:pk>/isporuceno/",
        DeliveryMarkDeliveredView.as_view(),
        name="mark_delivered",
    ),
    path("prodavnica/", ShopProfileView.as_view(), name="profile"),
]
