# Future Nova applications

Reserved application IDs and eventual source directories:

- `server-hub/`: Paper server lifecycle and management (not implemented).
- `store/`: application catalog (not implemented).
- `monitor/`: CPU/GPU/memory/temperature (not implemented).
- `settings/`: Nova preferences (not implemented).

Runtime apps: `/opt/nova/apps/<app-id>`, shared resources: `/opt/nova/shared`,
per-user state: `$XDG_DATA_HOME/nova` (default `~/.local/share/nova`).
System state: `/var/lib/nova`. Never run the desktop apps as root.
