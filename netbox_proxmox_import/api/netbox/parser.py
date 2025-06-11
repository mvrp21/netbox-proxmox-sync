import re


class NetBoxParser:

    # FIXME: this comes from the old idea, we're now creating the cluster first and THEN syncing it
    INFO = {
        "tag_color": "#d1d1d1",
        "cluster_name": "Proxmox C3SL",
        "cluster_type": "Proxmox",
        "cluster_description": "Production Proxmox Cluster",
        "vm_role": "Virtual Machine",
    }

    def __init__(self, remaps={}):
        for key in remaps:
            if key not in self.INFO:
                raise Exception(
                    f"Invalid key mapping ({key}). Supported keys are: {self.INFO.keys()}"
                )
            self.INFO[key] = remaps[key]

    def parse_tags(self, px_tags):
        nb_tags = []
        for name, color in px_tags.items():
            tag_slug = name.lower().replace(" ", "-").replace(".", "_")
            tag_color = self.INFO["tag_color"] if color is None else color
            nb_tags.append({
                "name": name,
                "slug": tag_slug,
                "color": tag_color,
                "object_types": ["virtualization.virtualmachine"],
            })
        return nb_tags

    def parse_vms(self, px_vm_list):
        nb_vms = []
        for vm in px_vm_list:
            nb_vms.append(self._parse_vm(vm))
        return nb_vms

    def _parse_vm(self, px_vm):
        vm_status = "active" if px_vm["status"] == "running" else "offline"
        nb_vm = {
            "name": px_vm["name"],
            "status": vm_status,
            "device": {"name": px_vm["node"]},
            "cluster": {"name": self.INFO["cluster_name"]},
            "vcpus": px_vm["sockets"] * px_vm["cores"],
            "memory": px_vm["memory"],
            "role": {"name": self.INFO["vm_role"]},
            "disk": int(px_vm["maxdisk"] / 2 ** 20),  # B -> MB
            "tags": [{"name": tag} for tag in px_vm["tags"]],
            # TODO: add custom field with plugin (or does it have to be done manually?)
            "custom_fields": {"vmid": px_vm["vmid"]},
        }
        return nb_vm

    def parse_vminterfaces(self, px_interface_list):
        nb_vminterfaces = []
        for px_interface in px_interface_list:
            mac, vlanid = self._extract_mac_vlan(px_interface["info"])
            interface = {
                # FIXME: VM name is possibly not unique
                "name": px_interface["name"],
                "virtual_machine": {"name": px_interface["vm"]},
                # FIXME: v4.2 breaks mac_address field
                "mac_address": mac,
                "mode": "access",
                "untagged_vlan": {"vid": vlanid},
            }
            nb_vminterfaces.append(interface)
        return nb_vminterfaces

    # TODO: allow custom VLAN extraction
    def _extract_mac_vlan(self, net_string):
        mac_match = re.search(r"([0-9A-Fa-f:]{17})", net_string)
        vlan_match = re.search(r"vmbr(\d+)", net_string)
        mac_address = mac_match.group(1) if mac_match else None
        vlan_id = vlan_match.group(1) if vlan_match else None
        return mac_address, vlan_id
