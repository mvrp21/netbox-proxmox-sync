from rest_framework import serializers

from netbox.api.serializers import NetBoxModelSerializer
from ..models import ProxmoxConnection

class ProxmoxConnectionSerializer(NetBoxModelSerializer):

    class Meta:
        model = ProxmoxConnection
        fields = (
            'id', 'cluster', 'url', 'user', 'sync_nodes',
            'custom_fields', 'created', 'last_updated',
        )
        url = serializers.HyperlinkedIdentityField(
            view_name='plugins-api:netbox_proxmox_import-api:connection-detail'
        )
