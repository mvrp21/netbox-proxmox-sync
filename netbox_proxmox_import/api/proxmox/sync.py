from proxmoxer import ProxmoxAPI

px = ProxmoxAPI(
    "proxmox.example.com",
    user="root@pam",
    token_name="netbox",
    token_value="yourtoken",
    verify_ssl=True,
)


#
def get_data():
    pass

def parse_data():
    pass

def sync():
    pass
