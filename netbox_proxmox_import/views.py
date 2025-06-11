from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from django.views import View

class ManagementView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "netbox_proxmox_import/management_page.html")
