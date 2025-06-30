import re


class NetBoxParser:


    def __init__(self, proxmox_connection):
        self.connection = proxmox_connection
        self.default_tag_color = "d1d1d1"


    def parse_tags(self, px_tags):
        nb_tags = []
        for name, color in px_tags.items():
            tag_slug = name.lower().replace(" ", "-").replace(".", "_")
            tag_slug = f"px_{self.connection.id}__{tag_slug}"
            tag_color = self.default_tag_color if color is None else color
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
            # Note: will not set the node for the VM if the node itself
            # is not assigned to the virtualization cluster of the VM
            "device": {"name": px_vm["node"]},
            "cluster": {"name": self.connection.cluster.name},
            "vcpus": int(px_vm["sockets"]) * int(px_vm["cores"]),
            "memory": int(px_vm["memory"]),
            # "role": self.connection.vm_role_id or None,
            "disk": int(px_vm["maxdisk"] / 2 ** 20),  # B -> MB
            "tags": [{"name": tag} for tag in px_vm["tags"]],
            "custom_fields": {"vmid": px_vm["vmid"]},
        }
        return nb_vm

    def parse_vminterfaces(self, px_interface_list):
        nb_vminterfaces = []
        for px_interface in px_interface_list:
            mac, vlanid = self._extract_mac_vlan(px_interface["info"])
            interface = {
                "name": px_interface["name"],
                "virtual_machine": {"name": px_interface["vm"]},
                # FIXME: v4.2 breaks mac_address field
                "mac_address": mac.upper(),
                "mode": "access",
                "untagged_vlan": {"vid": int(vlanid)},
            }
            nb_vminterfaces.append(interface)
        return nb_vminterfaces

    def _extract_mac_vlan(self, net_string):
        mac_match = re.search(r"([0-9A-Fa-f:]{17})", net_string)
        vlan_match = re.search(r"vmbr(\d+)", net_string)
        mac_address = mac_match.group(1) if mac_match else None
        vlan_id = vlan_match.group(1) if vlan_match else None
        return mac_address, vlan_id
