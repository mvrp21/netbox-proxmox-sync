from django.urls import path
from . import views, models
from netbox.views.generic import ObjectChangeLogView

urlpatterns = (
    path('connections/', views.ProxmoxConnectionListView.as_view(), name='connection_list'),
    path('connections/add', views.ProxmoxConnectionEditView.as_view(), name='connection_add'),
    path('connections/<int:pk>', views.ProxmoxConnectionView.as_view(), name='connection'),
    path('connections/<int:pk>/edit', views.ProxmoxConnectionEditView.as_view(), name='connection_edit'),
    path('connections/<int:pk>/delete', views.ProxmoxConnectionDeleteView.as_view(), name='connection_delete'),

    path('connections/<int:pk>/changelog', ObjectChangeLogView.as_view(), name='connection_changelog', kwargs={
        'model': models.ProxmoxConnection
    }),
)


