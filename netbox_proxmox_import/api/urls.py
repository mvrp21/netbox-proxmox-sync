from netbox.api.routers import NetBoxRouter
from . import views

app_name = 'netbox_proxmox_import'

router = NetBoxRouter()
router.register('connections', views.ProxmoxConnectionViewSet)

urlpatterns = router.urls
