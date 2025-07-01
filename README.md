# Proxmox to NetBox Integration Plugin

This is a NetBox plugin that fetches information from a Proxmox server and imports it into NetBox. It simply imports the data over nicely.

## Features

- Imports virtual machines (and their interfaces) from Proxmox into NetBox.
- Supports synchronization of multiple clusters.
- Complete management through the UI.
- Automatically updates device and node information at regular intervals (maybe? I'll see about that).

## Compatibility

| NetBox Version  | Plugin Version  |
|-----------------|-----------------|
| 4.1.x           | 1.0.0           |
| 4.2.x           | 1.1.0           |

## Installation

Regular plugin install.

1. Clone the repository and install:

```bash
cd /opt/netbox
sudo ./venv/bin/python3 netbox/manage.py makemigrations netbox_proxmox_import
sudo ./venv/bin/python3 netbox/manage.py migrate
```

2. Add the plugin to the `PLUGINS` netbox configuration:

```python
PLUGINS = ['netbox_proxmox_import']
```

3. Restart NetBox and apply migrations:

```bash
sudo systemctl restart netbox
cd /opt/netbox
sudo ./venv/bin/python3 netbox/manage.py migrate netbox_proxmox_import
```

And that's it!

## Usage

Create your virtualization cluster as you would normally.

This plugin adds a model called ProxmoxCluster, which stores the actual connection configuration to your Proxmox clusters. Access this page via the path `/plugins/nbp-sync/proxmox-connections` or using the sidebar, under "Plugins".

![Proxmox Connections Showcase](images/creation.png "Proxmox Connections Screen")

Each cluster connection gets its own configuration.

The current configuration options are:
- **Domain (required)**: URL to access the Proxmox cluster (check your firewall and DNS!).
- **User (required)**: Username to access the Proxmox API.
- **Access Token (required)**: Token for this user to use the Proxmox API.
- **Cluster (required)**: The actual cluster in NetBox this Proxmox connection will be associated to.

> [!caution]
> **Use a read-only Proxmox user! This plugin DOES NOT send writes to Proxmox!**

![Sidebar Showcase](images/sidebar.png "Sidebar")

After that you'll have a nice interface `/plugins/nbp-sync/proxmox-connections/<connection_id>`, from where you can manually synchronize the information.

![VM Showcase](images/vm_sync.png "VMs")

It will also show what has changed and also inform you of any warnings or errors.

![VMInterface Showcase](images/vmi_sync.png "VMInterfaces")

> [!note]
> The first sync generally takes the longest, as no information is present yet on NetBox, so we create everything.
>
> This plugin was tested on a 2 core 2GB VM with pretty standard RBD configuration, and the initial sync of ~140 VMs and ~170 VMInterfaces took roughly 70 seconds.
