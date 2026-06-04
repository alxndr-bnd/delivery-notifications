from django.urls import path

from .views import send_rating

app_name = "tasks"

urlpatterns = [
    path("send-rating/<int:delivery_id>/", send_rating, name="send_rating"),
]
