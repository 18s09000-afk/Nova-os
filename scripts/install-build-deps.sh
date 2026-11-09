#!/bin/sh
set -eu
[ "$(id -u)" -eq 0 ] || { echo 'Run as root in a Debian 13 amd64 build VM.' >&2; exit 1; }
# shellcheck disable=SC1091
. /etc/os-release
[ "$ID:$VERSION_ID:$(dpkg --print-architecture)" = debian:13:amd64 ] || {
 echo 'Debian 13 amd64 is required.' >&2; exit 1;
}
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
 live-build debootstrap debian-archive-keyring ca-certificates \
 xorriso squashfs-tools grub-pc-bin grub-efi-amd64-bin mtools dosfstools \
 isolinux syslinux-common qemu-system-x86 qemu-system-gui qemu-utils ovmf python3 shellcheck
