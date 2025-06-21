import json
from django.core.serializers import serialize
from extras.models import Tag
from virtualization.models import VirtualMachine
from dcim.models import Device
from django.forms.models import model_to_dict


class NetBoxUpdater:
    def __init__(self, proxmox_connection):
        self.connection = proxmox_connection
        self.devices = Device.objects.filter(cluster=proxmox_connection.cluster.id)

    def _vms_equal(self, px_vm, nb_vm):
        if nb_vm.device is None:
            return False
        if px_vm["device"]["name"] != nb_vm.device.name:
            return False
        if px_vm["status"] != nb_vm.status:
            return False
        if px_vm["vcpus"] != nb_vm.vcpus:
            return False
        if px_vm["memory"] != nb_vm.memory:
            return False
        if px_vm["disk"] != nb_vm.disk:
            return False
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
        return serialize("json", tags)
        # TODO: remove the missing ones??
        # How to know which tags the plugin is managing?

    def update_vms(self, parsed_vms):
        existing_vms = VirtualMachine.objects.filter(cluster=self.connection.cluster)
        existing_vms_by_name = {vm.name: vm for vm in existing_vms}

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
            VirtualMachine.objects.create(*vm)
        for vm in update:
            vm_entry = vm["before"]
            vm["before"] = {
                "name": vm_entry.name,
                "status": vm_entry.status,
                "device": None if vm_entry.device is None else {"name": vm_entry.device.name},
                "cluster": vm_entry.cluster.id,
                "vcpus": int(vm_entry.vcpus),
                "memory": vm_entry.memory,
                "disk": vm_entry.disk,
                # "tags": [{"name": tag.name} for tag in vm_entry.tags],
                "custom_fields": {"vmid": vm_entry.cf["vmid"]},
            }
            vm_entry.status = vm["after"]["status"]
            # vm_entry.device = vm["after"]["device"]
            vm_entry.vcpus = vm["after"]["vcpus"]
            vm_entry.memory = vm["after"]["memory"]
            vm_entry.disk = vm["after"]["disk"]
            vm_entry.custom_field_data["vmid"] = vm["after"]["custom_fields"]["vmid"]
            # vm_entry.tags = vm["after"]["tags"]
            vm_entry.save()
        for vm in delete:
            vm.delete()

        return json.dumps({
            'create': create,
            'update': update,
            'delete': delete,
        })
