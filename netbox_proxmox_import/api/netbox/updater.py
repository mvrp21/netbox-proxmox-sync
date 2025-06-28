import json
from django.core.serializers import serialize
from extras.models import Tag
from dcim.models import Device
from virtualization.models import VirtualMachine, VMInterface
from ipam.models import VLAN

class NetBoxUpdater:
    def __init__(self, proxmox_connection):
        self.connection = proxmox_connection
        self.devices_by_name = {}
        for device in Device.objects.filter(cluster=proxmox_connection.cluster.id):
            self.devices_by_name[device.name] = device
        self.tags_by_name = {}
        vlans = VLAN.objects.all()
        self.vlans_by_vid = {vlan.vid: vlan for vlan in vlans}
        self.vms_by_name = {}

    def update_tags(self, categorized_tags):
        tags = Tag.objects.bulk_create(
                [Tag(
                    name=tag_data["name"],
                    slug=tag_data["slug"],
                    color=tag_data["color"],
                    ) for tag_data in categorized_tags["update"]],
                update_conflicts=True,
                unique_fields=["slug"],
                update_fields=["name", "color"],
                )
        for tag in tags:
            self.tags_by_name[tag.name] = tag
        return serialize("json", tags)

    def update_vms(self, categorized_vms):
        create = categorized_vms["create"]
        update = categorized_vms["update"]
        delete = categorized_vms["delete"]
        errors = []
        warnings = categorized_vms["warnings"]
        # NetBox doesn't use bulk_create, so we won't either
        # Django's bulk methods behave weirdly anyways
        for vm in create:
            try:
                self.vms_by_name[vm["name"]] = VirtualMachine.objects.create(
                        name=vm["name"],
                        status=vm["status"],
                        device=self.devices_by_name.get(vm["device"]["name"]),
                        cluster=self.connection.cluster,
                        vcpus=vm["vcpus"],
                        memory=vm["memory"],
                        disk=vm["disk"],
                        # this "self.tags_by_name" does imply having to call update_tags() first
                        # tags=[self.tags_by_name.get(tag["name"]) for tag in vm["tags"]],
                        custom_field_data=vm["custom_fields"],
                        )
                self.vms_by_name[vm["name"]].tags.set([self.tags_by_name.get(tag["name"]) for tag in vm["tags"]])
                self.vms_by_name[vm["name"]].save()
            except Exception as e:
                errors.append(e)
        for vm in update:
            vm_entry = vm["before"]
            # We need to translate the before (a NetBox Model) into something JSON serializable
            vm["before"] = {
                    "name": vm_entry.name,
                    "status": vm_entry.status,
                    "device": None if vm_entry.device is None else {"name": vm_entry.device.name},
                    "cluster": vm_entry.cluster.id,
                    "vcpus": 0 if vm_entry.vcpus is None else int(vm_entry.vcpus),
                    "memory": vm_entry.memory,
                    "disk": vm_entry.disk,
                    "tags": [{"name": tag.name} for tag in vm_entry.tags.all()],
                    "custom_fields": {"vmid": vm_entry.cf["vmid"]},
                    }
            vm_entry.status = vm["after"]["status"]
            device_name = vm["after"]["device"]["name"]
            vm_entry.device = self.devices_by_name.get(device_name)
            vm_entry.vcpus = vm["after"]["vcpus"]
            vm_entry.memory = vm["after"]["memory"]
            vm_entry.disk = vm["after"]["disk"]
            vm_entry.custom_field_data["vmid"] = vm["after"]["custom_fields"]["vmid"]
            # this "self.tags_by_name" does imply having to call update_tags() first
            try:
                vm_entry.tags.set([self.tags_by_name.get(tag["name"]) for tag in vm["after"]["tags"]])
                vm_entry.save()
                self.vms_by_name[vm_entry.name] = vm_entry
            except Exception as e:
                errors.append(e)
        for vm in delete:
            try:
                vm.delete()
            except Exception as e:
                errors.append(e)

        return json.dumps({
            "create": create,
            "update": update,
            "delete": [{
                "name": vm.name,
                "status": vm.status,
                "device": None if vm.device is None else {"name": vm.device.name},
                "cluster": vm.cluster.id,
                "vcpus": 0 if vm.vcpus is None else int(vm.vcpus),
                "memory": vm.memory,
                "disk": vm.disk,
                # "tags": [{"name": tag.name} for tag in vm.tags.all()],
                "custom_fields": {"vmid": vm.cf["vmid"]},
                } for vm in delete],
            "errors": errors,
            "warnings": warnings,
        })
    def update_vminterfaces(self, categorized_vminterfaces):
        create = categorized_vminterfaces["create"]
        update = categorized_vminterfaces["update"]
        delete = categorized_vminterfaces["delete"]
        errors = []
        warnings = categorized_vminterfaces["warnings"]
        # NetBox doesn't use bulk_create, so we won't either
        # Django's bulk methods behave weirdly anyways
        for vmi in create:
            try:
                VMInterface.objects.create(
                    name=vmi["name"],
                    mac_address=vmi["mac_address"],
                    virtual_machine=self.vms_by_name.get(vmi["virtual_machine"]["name"]),
                    mode=vmi["mode"],
                    untagged_vlan=self.vlans_by_vid.get(vmi["untagged_vlan"]["vid"])
                )
            except Exception as e:
                errors.append(e)

        for vmi in update:
            vmi_entry = vmi["before"]
            vmi["before"] = {
                "name": vmi_entry.name,
                "virtual_machine": {"name": vmi_entry.virtual_machine.name},
                "mac_address": str(vmi_entry.mac_address),
                "mode": vmi_entry.mode,
                "untagged_vlan": None if vmi_entry.untagged_vlan is None else {"vid": vmi_entry.untagged_vlan.vid},
            }
            # this "self.vms_by_name" does imply having to call update_vms() first
            vmi_entry.mac_address = vmi["after"]["mac_address"]
            vmi_entry.mode = vmi["after"]["mode"]
            vlan_vid = vmi["after"]["untagged_vlan"]["vid"]
            netbox_vlan = self.vlans_by_vid.get(vlan_vid)
            vmi_entry.vlan = netbox_vlan
            try:
                vmi_entry.save()
            except Exception as e:
                errors.append(e)
        for vmi in delete:
            try:
                # FIXME: probably will raise an Exception if the vminterface was already cascade deleted by a vm deletion
                vmi.delete()
            except Exception as e:
                errors.append(e)

        return json.dumps({
            "create": create,
            "update": update,
            "delete": [{
                "name": vmi.name,
                "virtual_machine": {"name": vmi.virtual_machine.name},
                "mac_address": str(vmi.mac_address),
                "mode": "access",
                "untagged_vlan": None if vmi.untagged_vlan is None else {"vid": vmi.untagged_vlan.vid},
            } for vmi in delete],
            "errors": errors,
            "warnings": warnings,
        })
