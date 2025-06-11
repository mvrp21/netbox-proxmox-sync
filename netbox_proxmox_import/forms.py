from netbox.forms import NetBoxModelForm
from .models import ProxmoxConnection


class ProxmoxConnectionForm(NetBoxModelForm):

    class Meta:
        model = ProxmoxConnection
        fields = ('url', 'user', 'token_id', 'token_secret', 'sync_nodes', 'cluster')
