from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from django.views import View

# from .sync import ImportProxmoxCluster

class ButtonPageView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "netbox_proxmox_import/my_button_page.html")

class ExecuteActionView(View):
    def post(self, request, *args, **kwargs):
        # Your action goes here
        # For example, print a message or do something else.
        print("Button clicked!")
        return JsonResponse({"status": "success"})

