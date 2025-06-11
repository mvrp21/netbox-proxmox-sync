from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel


class ProxmoxConnection(NetBoxModel):

    def get_absolute_url(self):
        return reverse('plugins:netbox_proxmox_import:connection', args=[self.pk])

    def __str__(self):
        return self.cluster

    url = models.URLField(max_length=255)
    user = models.CharField(max_length=127)

    # FIXME: as the name suggests, should be secret to the UI
    token_id = models.CharField(max_length=127)
    token_secret = models.CharField(max_length=127)

    sync_nodes = models.BooleanField(default=False)

    cluster = models.ForeignKey(
        to='virtualization.cluster',
        on_delete=models.CASCADE,
        related_name='connections'
    )
