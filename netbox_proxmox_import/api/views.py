from django.http import HttpResponse
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from netbox_proxmox_sync.api.utils.errors import APIError
from netbox_proxmox_sync.api.proxmox import create, update, delete
import json
import traceback
# TODO: fix HTTP status codes
# TODO: proper error handling


class CreateCluster(PermissionRequiredMixin, View):
    permission_required = "nbp_sync.sync_proxmox_cluster"

    def get(self, _):
        try:
            result = create.all()
            json_result = json.dumps(result)
            return HttpResponse(json_result, content_type='application/json')
        except APIError as e:
            raise e
            json_result = json.dumps({'error': str(e), 'trace': traceback.print_exc()})
            return HttpResponse(
                json_result, status=e.status, content_type='application/json'
            )


class UpdateCluster(PermissionRequiredMixin, View):
    permission_required = "nbp_sync.sync_proxmox_cluster"

    def get(self, _):
        try:
            result = update.all()
            json_result = json.dumps(result)
            return HttpResponse(json_result, status=201, content_type='application/json')
        except APIError as e:
            raise e
            json_result = json.dumps({'error': str(e), 'trace': traceback.print_exc()})
            return HttpResponse(
                json_result, status=e.status, content_type='application/json'
            )


class DeleteCluster(PermissionRequiredMixin, View):
    permission_required = "nbp_sync.reset_promox_cluster"

    def get(self, _):
        try:
            result = delete.all()
            json_result = json.dumps(result)
            return HttpResponse(json_result, status=201, content_type='application/json')
        except APIError as e:
            raise e
            json_result = json.dumps({'error': str(e), 'trace': traceback.print_exc()})
            return HttpResponse(
                json_result, status=e.status, content_type='application/json'
            )
