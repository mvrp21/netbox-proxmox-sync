from proxmoxer import ProxmoxAPI


class Proxmox:

    vminterfaces = []

    def __init__(self, config):
        self.proxmox = ProxmoxAPI(
            config["host"],
            port=config["port"],
            user=config["user"],
            token_name=config["token"]["name"],
            token_value=config["token"]["value"],
            verify_ssl=config["verify_ssl"],
        )

    def get_tags(self):
        options = self.proxmox.cluster.options.get()
        tags = {}
        for tag in options["allowed-tags"]:
            tags[tag] = None
        for tag in options["tag-style"]["color-map"].split(';'):
            name = tag.split(':')[0]
            color = tag.split(':')[1]
            tags[name] = color
        return tags

    def get_cluster(self):
        return self.proxmox.cluster.status.get()[0]

    def get_vms(self):
        vm_resources = self.proxmox.cluster.resources.get(type="vm")
        vms = []
        for vm in vm_resources:
            vm_config = self.proxmox.nodes(vm['node']).qemu(vm['vmid']).config.get()
            self._add_vminterfaces(vm_config)
            # Store some status info for later
            vm_config["tags"] = [] if vm.get("tags") is None else vm["tags"].split(';')
            vm_config["maxdisk"] = int(vm["maxdisk"])
            vm_config["maxcpu"] = int(vm["maxcpu"])
            vm_config["vmid"] = vm["vmid"]
            vm_config["node"] = vm["node"]
            vm_config["status"] = vm["status"]
            vms.append(vm_config)
        return vms

    def _add_vminterfaces(self, vm_config):
        for key in vm_config:
            if key.startswith('net'):
                self.vminterfaces.append({
                    "vm": vm_config["name"],
                    "name": f"{vm_config['name']}:{key}",
                    "info": vm_config[key],
                })

    def get_vminterfaces(self):
        if len(self.vminterfaces) == 0:
            self.get_vms()
        return self.vminterfaces
