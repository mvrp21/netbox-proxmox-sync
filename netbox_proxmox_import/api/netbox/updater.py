import json
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.contrib.contenttypes.models import ContentType
from extras.models import Tag
from dcim.models import Device, MACAddress
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
            vm_contenttype = ContentType.objects.get(app_label="virtualization", model="virtualmachine")
            try:
                new_tag = Tag.objects.create(
                    name=tag["name"],
                    slug=tag["slug"],
                    color=tag["color"],
                    # object_types=[vm_contenttype]
                )
                new_tag.object_types.set([vm_contenttpe])
                created.append(new_tag)
            except Exception as e:
                errors.append(e)
        # ======================================================================================== #
        for tag in categorized_tags["update"]:
            updated_tag = tag["before"]
            updated_tag.slug = tag["after"]["slug"]
            updated_tag.color = tag["after"]["color"]
            try:
                updated_tag.save()
                updated_tag.object_types.set(["virtualization.virtualmachine"])
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
                tags = [ tags_by_name.get(tag["name"]) for tag in vm["tags"] ]
                new_vm.save()
                new_vm.tags.set([ tag for tag in tags if tag is not None ])
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
                tags = [ tags_by_name.get(tag["name"]) for tag in vm["after"]["tags"] ]
                updated_vm.save()
                updated_vm.tags.set([ tag for tag in tags if tag is not None ])
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
                    # mac_address=vmi["mac_address"],
                    primary_mac_address=MACAddress.objects.update_or_create(mac_address=vmi["mac_address"])[0],
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
            # updated_vmi.mac_address = vmi["after"]["mac_address"]
            updated_vmi.primary_mac_address = MACAddress.objects.update_or_create(mac_address=vmi["after"]["mac_address"])[0]
            updated_vmi.mode = vmi["after"]["mode"]
            updated_vmi.vlan = vlans_by_vid.get(vmi["after"]["untagged_vlan"]["vid"])
            updated_vmi.virtual_machine = vms_by_name.get(vmi["after"]["virtual_machine"]["name"])
            try:
                updated_vmi.save()
                updated.append(updated_vmi)
            except Exception as e:
                errors.append(e)
        # ======================================================================================== #
        for vmi in categorized_vminterfaces["delete"]:
            try:
                # FIXME: Should we also delete the MACAddress?
                vmi.delete()
                deleted.append(vmi)
            except ObjectDoesNotExist:
                # in case it was cascade-deleted by a VM deletion
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

    def create_mac_address(self, mac_address):
        return new_mac
