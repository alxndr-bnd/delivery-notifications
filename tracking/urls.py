from django.urls import path

from .views import rate, status, unsubscribe

app_name = "tracking"

urlpatterns = [
    path("<str:token>/", status, name="status"),
    path("<str:token>/oceni/", rate, name="rate"),
    path("<str:token>/odjava/", unsubscribe, name="unsubscribe"),
]
