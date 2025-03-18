from proxmox.connector import Proxmox
from netbox.parser import NetBoxParser
from netbox.insert import NetBoxInserter


# TODO: logging
class ProxmoxToNetBoxSync:
    def __init__(self, proxmox_config, remaps={}):
        self.proxmox = Proxmox(proxmox_config)
        self.transformer = NetBoxParser(remaps)
        self.netbox = NetBoxInserter()

    def sync_tags(self):
        px_tags = self.proxmox.get_tags()
        nb_tags = self.transformer.parse_tags(px_tags)
        return self.netbox.sync_tags(nb_tags)

    def sync_cluster(self):
        px_cluster = self.proxmox.get_cluster()
        nb_cluster = self.transformer.parse_cluster(px_cluster)
        return self.netbox.sync_cluster(nb_cluster)

    def sync_vms(self):
        px_vms = self.proxmox.get_vms()
        nb_vms = self.transformer.parse_vms(px_vms)
        return self.netbox.sync_vms(nb_vms)

    def sync_vminterfaces(self):
        px_vminterfaces = self.proxmox.get_vminterfaces()
        nb_vminterfaces = self.transformer.parse_vminterfaces(px_vminterfaces)
        return self.netbox.sync_vminterfaces(nb_vminterfaces)

    def run_full_sync(self):
        self.sync_tags()
        self.sync_cluster()
        self.sync_vms()
        self.sync_vminterfaces()
