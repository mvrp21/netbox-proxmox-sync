from django.urls import path
from . import views

app_name = "netbox_proxmox_import"

urlpatterns = (
    path('', views.Test.as_view(), name="test"),
)
