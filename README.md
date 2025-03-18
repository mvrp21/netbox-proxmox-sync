# Proxmox to NetBox Integration Plugin

> Placeholder README. gipity-ed this hard.

This is a NetBox plugin that fetches information from a Proxmox server and imports it into NetBox. It allows you to manage your Proxmox virtual machines, nodes, and related data within NetBox.

## Features

- Imports virtual machines from Proxmox into NetBox as devices.
- Syncs Proxmox node details (e.g., hostname, CPU, memory) into NetBox.
- Automatically updates device and node information at regular intervals.

## Installation

1. Clone the repository into your NetBox plugins directory:

    ```bash
   cd /opt/netbox/netbox/plugins
   git clone https://github.com/mvrp21/proxmox-netbox-sync.git proxmox_to_netbox

2. Install any required dependencies (e.g., requests, proxmoxer):

    ```bash
    pip install -r /opt/netbox/netbox/plugins/nbp-sync/requirements.txt
    ```

3. Add the plugin to the `PLUGINS` list in your `configuration.py`:V

    ```python
    PLUGINS = [
        'proxmox_netbox_sync',
    ]
    ```

4. Configure the Proxmox API credentials in the plugin settings (`proxmox_to_netbox/settings.py`):

    ``` pythoj
    # Imporntant! Use a READ-ONLY API KEY! This plugin DOES NOT WRITE TO PROXMOX!
    PROXMOX_API_URL = 'https://your.proxmox.server:8006/api2/json'
    PROXMOX_API_USER = 'root@pam'
    PROXMOX_API_PASSWORD = 'yourpassword'
    ```
