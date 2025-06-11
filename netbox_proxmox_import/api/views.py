from netbox.api.viewsets import NetBoxModelViewSet

from .. import models
from .serializers import ProxmoxConnectionSerializer

class ProxmoxConnectionViewSet(NetBoxModelViewSet):
    queryset = models.ProxmoxConnection.objects.prefetch_related('tags')
    serializer_class = ProxmoxConnectionSerializer
