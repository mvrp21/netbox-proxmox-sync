import json

from .proxmox.connector import Proxmox
from .. import models


def sync_cluster(connection_id):
    proxmox_connection = models.ProxmoxConnection.objects.get(pk=connection_id)
    return json.dumps(get_proxmox_data(proxmox_connection))


def get_proxmox_data(proxmox_connection):
    # TODO: connection error handling here
    px = Proxmox({
        'host': proxmox_connection.domain,
        'port': proxmox_connection.port,
        'user': proxmox_connection.user,
        'token': {
            'name': proxmox_connection.token_id,
            'value': proxmox_connection.token_secret,
        },
        'verify_ssl': proxmox_connection.verify_ssl,
    })
    return {
        'cluster': px.get_cluster(),
        'tags': px.get_tags(),
        'vms': px.get_vms(),
        'vminterfaces': px.get_vminterfaces(),
    }

def update_netbox(proxmox_data):
    pass
