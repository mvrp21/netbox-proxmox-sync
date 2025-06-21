import json

from django.contrib.contenttypes.models import ContentType
from extras.models import CustomField
from virtualization.models import VirtualMachine


from .proxmox.connector import Proxmox
from .netbox.parser import NetBoxParser
from .netbox.updater import NetBoxUpdater
from .. import models


def sync_cluster(connection_id):
    # silently try to create or update the VMID custom field
    vm_contenttype = ContentType.objects.get(app_label='virtualization', model='virtualmachine')
    vmid, created = CustomField.objects.update_or_create(
        name='vmid',
        label="[Proxmox] VM ID",
        description="[Proxmox] VM ID",
        filter_logic="exact",
        type='integer',
        # object_types=[vm_contenttype.id],
        required=True,
    )
    vmid.object_types.set([vm_contenttype.id])

    proxmox_connection = models.ProxmoxConnection.objects.get(pk=connection_id)
    proxmox_data = get_proxmox_data(proxmox_connection)
    parsed_data = parse_proxmox_data(proxmox_connection, proxmox_data)
    returned = update_netbox(proxmox_connection, parsed_data)
    return json.dumps(returned)


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

def parse_proxmox_data(connection, proxmox_data):
    nb = NetBoxParser(connection)
    return {
        'tags': nb.parse_tags(proxmox_data['tags']),
        'vms': nb.parse_vms(proxmox_data['vms']),
        'vminterfaces': nb.parse_vminterfaces(proxmox_data['vminterfaces']),
    }

def update_netbox(connection, parsed_data):
    nb = NetBoxUpdater(connection)
    return {
        'tags': json.loads(nb.update_tags(parsed_data['tags'])),
        'vms': json.loads(nb.update_vms(parsed_data['vms'])),
        # 'vminterfaces': nb.update_vminterfaces(parsed_data['vminterfaces']),
    }
