import json
from django.core.serializers import serialize
from extras.models import Tag
from dcim.models import Device
from virtualization.models import VirtualMachine, VMInterface
from ipam.models import VLAN

# FIXME: kinda got rid of before/after in the update field

class NetBoxUpdater:
    def __init__(self, proxmox_connection):
        self.connection = proxmox_connection

    def update_tags(self, categorized_tags):
        errors = []
        created = []
        updated = []
        deleted = []

        for tag in categorized_tags["create"]:
            try:
                new_tag = Tag.objects.create(
                    name=tag["name"],
                    slug=tag["slug"],
                    color=tag["color"],
                    # object_types=["virtualization.virtualmachine"]
                )
                new_tag.object_types.set(["virtualization.virtualmachine"])
                created.append(new_tag)
            except Exception as e:
                errors.append(e)
        # ======================================================================================== #
        for tag in categorized_tags["update"]:
            updated_tag = tag["before"]
            updated_tag.slug = tag["after"]["slug"]
            updated_tag.color = tag["after"]["color"]
            try:
                updated_tag.object_types.set(["virtualization.virtualmachine"])
                updated_tag.save()
                created.append(updated_tag)
            except Exception as e:
                errors.append(e)
        # ======================================================================================== #
        for tag in categorized_tags["delete"]:
            try:
                tag.delete()
                deleted.append(tag)
            except Exception as e:
                errors.append(e)

        return {
            "created": json.loads(serialize("json", created)),
            "updated": json.loads(serialize("json", updated)),
            "deleted": json.loads(serialize("json", deleted)),
            "errors": [str(e) for e in errors],
            "warnings": categorized_tags["warnings"]
        }

    def update_vms(self, categorized_vms):
        errors = []
        created = []
        updated = []
        deleted = []

        tags_by_name = {
            t.name: t for t in Tag.objects.filter(slug__istartswith=f"px_{self.connection.id}__")
        }
        devices_by_name = {
            device.name: device for device in Device.objects.filter(cluster=self.connection.cluster)
        }

        for vm in categorized_vms["create"]:
            try:
                new_vm = VirtualMachine.objects.create(
                        name=vm["name"],
                        status=vm["status"],
                        device=devices_by_name.get(vm["device"]["name"]),
                        cluster=self.connection.cluster,
                        vcpus=vm["vcpus"],
                        memory=vm["memory"],
                        disk=vm["disk"],
                        # tags=[tags_by_name.get(tag["name"]) for tag in vm["tags"]],
                        custom_field_data=vm["custom_fields"],
                        )
                new_vm.tags.set([
                    tags_by_name.get(tag["name"]) for tag in vm["tags"]
                ])
                new_vm.save()
                created.append(new_vm)
            except Exception as e:
                errors.append(e)
        # ======================================================================================== #
        for vm in categorized_vms["update"]:
            updated_vm = vm["before"]
            updated_vm.status = vm["after"]["status"]
            updated_vm.vcpus = vm["after"]["vcpus"]
            updated_vm.memory = vm["after"]["memory"]
            updated_vm.disk = vm["after"]["disk"]
            updated_vm.custom_field_data["vmid"] = vm["after"]["custom_fields"]["vmid"]
            updated_vm.device = devices_by_name.get(vm["after"]["device"]["name"])
            try:
                updated_vm.tags.set([
                    tags_by_name.get(tag["name"]) for tag in vm["after"]["tags"]
                ])
                updated_vm.save()
                updated.append(updated_vm)
            except Exception as e:
                errors.append(e)
        # ======================================================================================== #
        for vm in categorized_vms["delete"]:
            try:
                vm.delete()
                deleted.append(vm)
            except Exception as e:
                errors.append(e)

        return {
            "created": json.loads(serialize("json", created)),
            "updated": json.loads(serialize("json", updated)),
            "deleted": json.loads(serialize("json", deleted)),
            "errors": [str(e) for e in errors],
            "warnings": categorized_vms["warnings"]
        }
    def update_vminterfaces(self, categorized_vminterfaces):
        errors = []
        created = []
        updated = []
        deleted = []

        vms_by_name = {
            vm.name: vm for vm in VirtualMachine.objects.filter(cluster=self.connection.cluster)
        }
        vlans_by_vid = { vlan.vid: vlan for vlan in VLAN.objects.all() }

        for vmi in categorized_vminterfaces["create"]:
            try:
                new_vmi = VMInterface.objects.create(
                    name=vmi["name"],
                    mac_address=vmi["mac_address"],
                    virtual_machine=vms_by_name.get(vmi["virtual_machine"]["name"]),
                    mode=vmi["mode"],
                    untagged_vlan=vlans_by_vid.get(vmi["untagged_vlan"]["vid"]),
                )
                created.append(new_vmi)
            except Exception as e:
                errors.append(e)
        # ======================================================================================== #
        for vmi in categorized_vminterfaces["update"]:
            updated_vmi = vmi["before"]
            updated_vmi.mac_address = vmi["after"]["mac_address"]
            updated_vmi.mode = vmi["after"]["mode"]
            updated_vmi.vlan = vlans_by_vid.get(vmi["after"]["untagged_vlan"]["vid"])
            try:
                updated_vmi.save()
                updated.append(updated_vmi)
            except Exception as e:
                errors.append(e)
        # ======================================================================================== #
        for vmi in categorized_vminterfaces["delete"]:
            try:
                vmi.delete()
                deleted.append(vmi)
            except Exception as e:
                errors.append(e)

        return {
            "created": json.loads(serialize("json", created)),
            "updated": json.loads(serialize("json", updated)),
            "deleted": json.loads(serialize("json", deleted)),
            "errors": [str(e) for e in errors],
            "warnings": categorized_vminterfaces["warnings"],
        }
