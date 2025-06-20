from setuptools import find_packages, setup

setup(
    name = 'netbox_proxmox_import',
    version = '0.5',
    description = 'NetBox plugin to Import Proxmox Cluster data.',
    install_requires=['proxmoxer'],
    packages = find_packages(),
    include_package_data=True,
    package_data={"netbox_proxmox_import": ["templates/**/*.html"]},
    zip_safe=False,
)
