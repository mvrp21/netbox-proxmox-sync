from netbox.api.viewsets import NetBoxModelViewSet

from django.http import HttpResponse
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin

from .. import models
from .serializers import ProxmoxConnectionSerializer
from .sync import sync_cluster


class ProxmoxConnectionViewSet(NetBoxModelViewSet):
    queryset = models.ProxmoxConnection.objects.prefetch_related('tags')
    serializer_class = ProxmoxConnectionSerializer



class Sync(PermissionRequiredMixin, View):
    permission_required = "nbp_sync.sync_proxmox_cluster"

    def post(self, _, connection_id):
        json_result = sync_cluster(connection_id)
        return HttpResponse(
            json_result, status=200, content_type='application/json'
        )
