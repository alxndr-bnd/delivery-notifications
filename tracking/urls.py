from django.urls import path

from .views import rate, status

app_name = "tracking"

urlpatterns = [
    path("<str:token>/", status, name="status"),
    path("<str:token>/oceni/", rate, name="rate"),
]
