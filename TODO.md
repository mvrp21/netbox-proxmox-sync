# ToDo
1. [x] Improve error handling (good enough)
2. [x] Render JSON output from API call in the template
3. [x] Turn Proxmox Token into secret usin `netbox-secrets` (not doing it. if the attacker has access to the DB he already can see whatever he'd be able to see with the plugin, assuming the proxmox user is read-only)
4. [ ] Better README.md + images
5. [ ] Update to Netbox 4.2+
6. [ ] Fix any release errors or installation instructions

## "Extra"
- [ ] SyncNodes option?
- [ ] "Force" option?
- [ ] Allow VM/device/whatever ignore list
- [ ] Allow custom VLAN VID extraction (current is just `vmbr<VID>`)
