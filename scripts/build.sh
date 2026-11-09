#!/bin/bash
set -Eeuo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
[[ $EUID == 0 ]] || { echo 'Use sudo ./scripts/build.sh in a Debian 13 build VM.' >&2; exit 1; }
[[ $(dpkg --print-architecture) == amd64 ]] || { echo 'amd64 required' >&2; exit 1; }
for tool in lb debootstrap xorriso mksquashfs mount chroot; do
 command -v "$tool" >/dev/null || { echo "Missing $tool; run scripts/install-build-deps.sh" >&2; exit 1; }
done
# Probe only a temporary directory: never inspect or mount physical disks.
probe=$(mktemp -d)
trap 'rmdir "$probe" 2>/dev/null || true' EXIT
if ! mount -t tmpfs -o size=1m tmpfs "$probe"; then
 echo 'Build blocked: mount permission required. Use a full Debian VM, not a restricted container.' >&2
 exit 1
fi
umount "$probe"
rmdir "$probe"
trap - EXIT
mkdir -p "$ROOT/build" "$ROOT/dist"
exec 9>"$ROOT/build/.lock"
flock -n 9 || { echo 'Another build is running' >&2; exit 1; }
# Each run is isolated; failed build trees remain available for diagnostics.
work=$(mktemp -d "$ROOT/build/run-XXXXXXXX")
cp -a "$ROOT/auto" "$ROOT/config" "$work/"
cd "$work"
jobs=${NOVA_JOBS:-2}
[[ $jobs =~ ^[1-9][0-9]*$ ]] || { echo "Invalid NOVA_JOBS" >&2; exit 1; }
export MKSQUASHFS_OPTIONS="-processors $jobs"
# live-build passes MKSQUASHFS_OPTIONS to squashfs-tools.
./auto/config --chroot-squashfs-compression-type xz
set +e
lb build 2>&1 | tee "$ROOT/dist/build.log"
result=${PIPESTATUS[0]}
set -e
(( result == 0 )) || { echo "Build failed ($result). See dist/build.log and $work" >&2; exit "$result"; }
iso=$(find "$work" -maxdepth 1 -name '*.hybrid.iso' -print -quit)
[[ -n "$iso" ]] || { echo 'live-build produced no hybrid ISO' >&2; exit 1; }
cp "$iso" "$ROOT/dist/nova-os-0.1-amd64.iso"
cp "$work"/*.packages "$ROOT/dist/" 2>/dev/null || true
cd "$ROOT/dist"
sha256sum nova-os-0.1-amd64.iso > nova-os-0.1-amd64.iso.sha256
xorriso -indev nova-os-0.1-amd64.iso -report_el_torito plain > boot-catalog.txt 2>&1
printf 'Built: %s/dist/nova-os-0.1-amd64.iso\n' "$ROOT"
