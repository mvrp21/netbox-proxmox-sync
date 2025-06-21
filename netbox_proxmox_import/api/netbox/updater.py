import json
from django.core.serializers import serialize
from extras.models import Tag
from dcim.models import Device
from virtualization.models import VirtualMachine, VMInterface


class NetBoxUpdater:
    def __init__(self, proxmox_connection):
        self.connection = proxmox_connection
        self.devices_by_name = {}
        for device in Device.objects.filter(cluster=proxmox_connection.cluster.id):
            self.devices_by_name[device.name] = device
        self.tags_by_name = {}
        self.vms_by_name = {}
        self.cascade_deleted_vminterfaces = []

    def _vms_equal(self, px_vm, nb_vm):
        if nb_vm.device is None and self.devices_by_name.get(px_vm["device"]["name"]) is not None:
            return False
        if nb_vm.device is not None and px_vm["device"]["name"] != nb_vm.device.name:
            return False
        if px_vm["status"] != nb_vm.status:
            return False
        if px_vm["vcpus"] != nb_vm.vcpus:
            return False
        if px_vm["memory"] != nb_vm.memory:
            return False
        if px_vm["disk"] != nb_vm.disk:
            return False
        # TODO: detect tags were changed
        return True

    def update_tags(self, parsed_tags):
        tags = Tag.objects.bulk_create(
            [Tag(
                name=tag_data["name"],
                slug=tag_data["slug"],
                color=tag_data["color"],
            ) for tag_data in parsed_tags],
            update_conflicts=True,
            unique_fields=["slug"],
            update_fields=["name", "color"],
        )
        for tag in tags:
            self.tags_by_name[tag.name] = tag
        return serialize("json", tags)
        # TODO: remove the missing ones??
        # How to know which tags the plugin is managing?

    # TODO: error handling
    def update_vms(self, parsed_vms):
        existing_vms = VirtualMachine.objects.filter(cluster=self.connection.cluster)
        existing_vms_by_name = {vm.name: vm for vm in existing_vms}
        for name in existing_vms_by_name:
            self.vms_by_name[name] = existing_vms_by_name[name]

        create = []
        update = []
        delete = []

        for px_vm in parsed_vms:
            if px_vm["name"] not in existing_vms_by_name:
                create.append(px_vm)
            else:
                nb_vm = existing_vms_by_name[px_vm["name"]]
                if not self._vms_equal(px_vm, nb_vm):
                    update.append({"before": nb_vm, "after": px_vm})

        existing_vms_set = set(existing_vms_by_name.keys())
        parsed_vms_set = set(vm['name'] for vm in parsed_vms)
        deleted_vms_set = existing_vms_set - parsed_vms_set
        for vm_name in deleted_vms_set:
            delete.append(existing_vms_by_name[vm_name])

        # NetBox doesn't use bulk_create, so we won't either
        # Django's bulk methods behave weirdly anyways
        for vm in create:
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
        for vm in update:
            vm_entry = vm["before"]
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
            vm_entry.device = self.devices_by_name.get(vm["after"]["device"]["name"])
            vm_entry.vcpus = vm["after"]["vcpus"]
            vm_entry.memory = vm["after"]["memory"]
            vm_entry.disk = vm["after"]["disk"]
            vm_entry.custom_field_data["vmid"] = vm["after"]["custom_fields"]["vmid"]
            # this "self.tags_by_name" does imply having to call update_tags() first
            vm_entry.tags.set([self.tags_by_name.get(tag["name"]) for tag in vm["after"]["tags"]])
            vm_entry.save()
            self.vms_by_name[vm_entry.name] = vm_entry
        for vm in delete:
            del self.vms_by_name[vm.name]
            self.cascade_deleted_vminterfaces.extend(vm.interfaces.all())
            vm.delete()

        return json.dumps({
            'create': create,
            'update': update,
            'delete': [{
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
        })
    def _vminterfaces_equal(self, px_vmi, nb_vmi):
        if px_vmi["name"] != nb_vmi.name:
            return False
        if str(px_vmi["mac_address"]).lower() != str(nb_vmi.mac_address).lower():
            return False
        # TODO: detect vlan change
        return True

    def update_vminterfaces(self, parsed_vminterfaces):
        vms = [self.vms_by_name[name] for name in self.vms_by_name]
        existing_vminterfaces = VMInterface.objects.filter(virtual_machine__in=vms)
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
        parsed_vminterfaces_set = set(vmi['name'] for vmi in parsed_vminterfaces)
        deleted_vminterfaces_set = existing_vminterfaces_set - parsed_vminterfaces_set
        for vmi_name in deleted_vminterfaces_set:
            delete.append(existing_vminterfaces_by_name[vmi_name])

        # NetBox doesn't use bulk_create, so we won't either
        # Django's bulk methods behave weirdly anyways
        for vmi in create:
            VMInterface.objects.create(
                name=vmi["name"],
                mac_address=vmi["mac_address"],
                virtual_machine=self.vms_by_name.get(vmi["virtual_machine"]["name"]),
                mode=vmi["mode"],
            )
        for vmi in update:
            vmi_entry = vmi["before"]
            vmi["before"] = {
                "name": vmi_entry.name,
                "virtual_machine": {"name": vmi_entry.virtual_machine.name},
                "mac_address": str(vmi_entry.mac_address),
                "mode": vmi_entry.mode,
                # "untagged_vlan": vmi_entry.vlan,
            }
            # this "self.vms_by_name" does imply having to call update_vms() first
            vmi_entry.virtual_machine = self.vms_by_name.get(vmi["after"]["virtual_machine"]["name"])
            vmi_entry.mac_address = vmi["after"]["mac_address"]
            vmi_entry.mode = vmi["after"]["mode"]
            # vmi_entry.vlan = vmi["after"]["vlan"]
            vmi_entry.save()
        for vmi in delete:
            vmi.delete()
        delete.extend(self.cascade_deleted_vminterfaces)

        return json.dumps({
            'create': create,
            'update': update,
            'delete': [{
                "name": vmi.name,
                "virtual_machine": {"name": vmi.virtual_machine.name},
                "mac_address": str(vmi.mac_address),
                "mode": "access",
            } for vmi in delete],
        })
