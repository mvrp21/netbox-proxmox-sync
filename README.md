# Proxmox to NetBox Integration Plugin

This is a NetBox plugin that fetches information from a Proxmox server and imports it into NetBox. It simply imports the data over nicely.

## Features

- Imports virtual machines from Proxmox into NetBox.
- Supports synchronization of multiple clusters.
- Can sync Proxmox node details (e.g., hostname, CPU, memory) into NetBox, if desired (not supported just yet).
- Complete management through the UI.
- Automatically updates device and node information at regular intervals (maybe? I'll see about that).

## Installation

Hold on, didn't even finish this just yet. (getting close now)

## Usage

Create you virtualization cluster as you would normally.

This plugin adds a model called ProxmoxCluster, which stores the actual connection configuration to your Proxmox clusters. Access this page via the path `/plugins/nbp-sync/proxmox-connections` or using the sidebar, under "Plugins".

Each cluster connection gets its own configuration.

Configuration options are (could//may//will be, but whatever):
- **Domain (required)**: URL to access the Proxmox cluster (check your firewall and DNS!).
- **User (required)**: Username to access the Proxmox API.
- **Access Token (required)**: Token for this user to use the Proxmox API.
- **Sync Nodes(default=False)**: If the plugin should also import the information from the nodes or not. Note that if there are conflicts (node does not exist and should / node information does not match, etc.) the plugin will fail to synchronize the data and will inform you of the errors encountered.
- **Cluster**: The actual cluster in NetBox this Proxmox connection will be associated to.

**Use a read-only Proxmox user! This plugin DOES NOT send writes to Proxmox!**

Note: when deleting a cluster connection all the related information will be deleted with it, such as VMs, but also the Nodes if you configured the connection to manage them too.

After that you'll have a nice interface `/plugins/nbp-sync/proxmox-connections/<connection_id>`, from where you can manually synchronize the information. It will also show what has changed and also inform you of any warnings or errors.

> [!note]
> The first sync generally takes the longest, as no information is present yet on NetBox, so we create everything.
>
> This plugin was tested on a 2 core 2GB VM with pretty standard RBD configuration, and the initial sync of ~140 VMs and 170 VMInterfaces took around 70 seconds.
