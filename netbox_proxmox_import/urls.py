from django.urls import path
from . import views

app_name = "netbox_proxmox_import"

urlpatterns = (
    path('', views.ButtonPageView.as_view(), name="button_page"),
    path('execute/', views.ExecuteActionView.as_view(), name="execute_action"),
)
