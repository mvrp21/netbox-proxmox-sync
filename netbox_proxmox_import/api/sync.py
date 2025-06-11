import json

from .proxmox.connector import Proxmox
from .netbox.parser import NetBoxParser
from .. import models


def sync_cluster(connection_id):
    proxmox_connection = models.ProxmoxConnection.objects.get(pk=connection_id)
    proxmox_data = get_proxmox_data(proxmox_connection)
    return json.dumps(parse_proxmox_data(proxmox_data))


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

def parse_proxmox_data(proxmox_data):
    nb = NetBoxParser()
    return {
        'tags': nb.parse_tags(proxmox_data['tags']),
        'vms': nb.parse_vms(proxmox_data['vms']),
        'vminterfaces': nb.parse_vminterfaces(proxmox_data['vminterfaces']),
    }

def update_netbox(parsed_data):
    pass
