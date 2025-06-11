from netbox.views import generic
from . import forms, models, tables


class ProxmoxConnectionView(generic.ObjectView):
    queryset = models.ProxmoxConnection.objects.all()

class ProxmoxConnectionListView(generic.ObjectListView):
    queryset = models.ProxmoxConnection.objects.all()
    table = tables.ProxmoxConnectionTable

class ProxmoxConnectionEditView(generic.ObjectEditView):
    queryset = models.ProxmoxConnection.objects.all()
    form = forms.ProxmoxConnectionForm

class ProxmoxConnectionDeleteView(generic.ObjectDeleteView):
    queryset = models.ProxmoxConnection.objects.all()
