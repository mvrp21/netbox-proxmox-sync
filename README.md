# Proxmox to NetBox Integration Plugin

> Placeholder README. gipity-ed this hard.

This is a NetBox plugin that fetches information from a Proxmox server and imports it into NetBox. It allows you to manage your Proxmox virtual machines, nodes, and related data within NetBox.

## Features

- Imports virtual machines from Proxmox into NetBox as devices.
- Supports synchronization of multiple clusters.
- Can sync Proxmox node details (e.g., hostname, CPU, memory) into NetBox, if desired.
- Complete management through the UI.
- Automatically updates device and node information at regular intervals (maybe? I'll see about that).

## Installation

Hold on, didn't even finish this just yet.

## Usage

Create you virtualization cluster as you would normally.

This plugin adds a model called ProxmoxCluster, which stores the actual connection configuration to your Proxmox clusters. Access this page via the path `/plugins/nbp-sync/clusters` or using the sidebar, under "plugins".

Maybe "ProxmoxConnection" is a better name?

Each cluster connection gets its own configuration.

Configuration options are (could//may//will be, but whatever):
- **Cluster URL (required)**: URL to access the Proxmox cluster (check your firewall and DNS!).
- **User (required)**: Username to access the Proxmox API.
- **Access Token (required)**: Token for this user to use the Proxmox API.
- **Sync Nodes(default=False)**: If the plugin should also import the information from the nodes or not. Note that if there are conflicts (node does not exist and should / node information does not match, etc.) the plugin will fail to synchronize the data and will inform you of the errors encountered.

**Use a read-only Proxmox user! This plugin DOES NOT send writes to Proxmox!**

Note: when deleting a cluster connection all the related information will be deleted with it, such as VMs, but also the Nodes if you configured the connection to manage them too.
