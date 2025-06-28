import json
from django.core.serializers import serialize
from extras.models import Tag
from dcim.models import Device
from virtualization.models import VirtualMachine, VMInterface
from ipam.models import VLAN


class NetBoxCategorizer:
    def __init__(self, proxmox_connection):
        self.connection = proxmox_connection
        self.devices_by_name = {}
        self.devices_by_name = {
            device.name: device for device in
            Device.objects.filter(cluster=proxmox_connection.cluster.id)
        }
        self.vlans_by_vid = {vlan.vid: vlan for vlan in VLAN.objects.all()}
        self.tags_by_name = {}
        self.existing_vms = []
        self.existing_vms_by_name = {}

        self.vm_warnings = []
        self.vminterface_warnings = []

    def _vms_equal(self, px_vm, nb_vm):
        if self.devices_by_name.get(px_vm["device"]["name"]) is None:
            self.vm_warnings.append(
                f"Device for VM {px_vm['name']} "
                f"(DeviceName={px_vm['device']['name']}) "
                "not found!"
            )
        else:
            if nb_vm.device is None:
                return False
            elif px_vm["device"]["name"] != nb_vm.device.name:
                return False
        if px_vm["status"] != nb_vm.status:
            return False
        if px_vm["vcpus"] != nb_vm.vcpus:
            return False
        if px_vm["memory"] != nb_vm.memory:
            return False
        if px_vm["disk"] != nb_vm.disk:
            return False
        px_tags = set([tag["name"] for tag in px_vm["tags"]])
        nb_tags = set([tag.name for tag in nb_vm.tags.all()])
        if px_tags != nb_tags:
            return False
        return True

    def categorize_tags(self, parsed_tags):
        # FIXME: find a way to properly manage proxmox cluster tags
        # (Probably need to mess with the slug or add a custom_field)
        # Slug seems more reasonable, something like: px_<cluster_name>_<tag_slug> might do the trick
        return {
            "create": [],
            "update": parsed_tags,
            "delete": [],
        }

    def categorize_vms(self, parsed_vms):
        self.existing_vms = VirtualMachine.objects.filter(cluster=self.connection.cluster)
        self.existing_vms_by_name = {vm.name: vm for vm in self.existing_vms}

        create = []
        update = []
        delete = []

        for px_vm in parsed_vms:
            if px_vm["name"] not in self.existing_vms_by_name:
                create.append(px_vm)
            else:
                nb_vm = self.existing_vms_by_name[px_vm["name"]]
                if not self._vms_equal(px_vm, nb_vm):
                    update.append({"before": nb_vm, "after": px_vm})

        existing_vms_set = set(self.existing_vms_by_name.keys())
        parsed_vms_set = set(vm["name"] for vm in parsed_vms)
        deleted_vms_set = existing_vms_set - parsed_vms_set
        for vm_name in deleted_vms_set:
            delete.append(self.existing_vms_by_name[vm_name])

        return {
            "create": create,
            "update": update,
            "delete": delete,
            "warnings": self.vm_warnings,
        }
    def _vminterfaces_equal(self, px_vmi, nb_vmi):
        if self.vlans_by_vid.get(px_vmi["untagged_vlan"]["vid"]) is None:
            self.vminterface_warnings.append(
                f"Untagged VLAN for VMInterface {px_vmi['name']} "
                f"(VID={px_vmi['untagged_vlan']['vid']}) "
                "not found!"
            )
        else:
            if nb_vmi.untagged_vlan is None:
                return False
            elif int(px_vmi["untagged_vlan"]["vid"]) != int(nb_vmi.untagged_vlan.vid):
                return False
        if px_vmi["name"] != nb_vmi.name:
            return False
        if str(px_vmi["mac_address"]).upper() != str(nb_vmi.mac_address).upper():
            return False
        return True

    def categorize_vminterfaces(self, parsed_vminterfaces):
        existing_vminterfaces = VMInterface.objects.filter(virtual_machine__in=self.existing_vms)
        existing_vminterfaces_by_name = {vmi.name: vmi for vmi in existing_vminterfaces}

        create = []
        update = []
        delete = []

        for px_vmi in parsed_vminterfaces:
            if px_vmi["name"] not in existing_vminterfaces_by_name:
                create.append(px_vmi)
            else:
                nb_vmi = existing_vminterfaces_by_name[px_vmi["name"]]
                if not self._vminterfaces_equal(px_vmi, nb_vmi):
                    update.append({"before": nb_vmi, "after": px_vmi})

        existing_vminterfaces_set = set(existing_vminterfaces_by_name.keys())
        parsed_vminterfaces_set = set(vmi["name"] for vmi in parsed_vminterfaces)
        deleted_vminterfaces_set = existing_vminterfaces_set - parsed_vminterfaces_set
        for vmi_name in deleted_vminterfaces_set:
            delete.append(existing_vminterfaces_by_name[vmi_name])

        return {
            "create": create,
            "update": update,
            "delete": delete,
            "warnings": self.vminterface_warnings,
        }
