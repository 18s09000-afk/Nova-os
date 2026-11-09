#!/bin/bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
iso=${1:-"$ROOT/dist/nova-os-0.1-amd64.iso"}
[[ -f "$iso" ]] || { echo "ISO not found: $iso" >&2; exit 1; }
firmware=${OVMF_CODE:-/usr/share/OVMF/OVMF_CODE_4M.fd}
vars=${OVMF_VARS:-/usr/share/OVMF/OVMF_VARS_4M.fd}
[[ -f "$firmware" && -f "$vars" ]] || { echo 'Install ovmf or set OVMF_CODE and OVMF_VARS.' >&2; exit 1; }
run=$(mktemp -d)
trap 'rm -rf -- "$run"' EXIT
mkdir -p "$ROOT/dist"
cp "$vars" "$run/vars.fd"
printf "QEMU monitor: %s/monitor.sock\n" "$run"
accel=tcg
[[ -r /dev/kvm && -w /dev/kvm ]] && accel=kvm
# No host block device and no virtual writable hard disk is attached.
qemu-system-x86_64 -machine "q35,accel=$accel" -cpu max -m "${NOVA_RAM_MB:-4096}" -smp 2 \
 -drive "if=pflash,format=raw,readonly=on,file=$firmware" \
 -drive "if=pflash,format=raw,file=$run/vars.fd" \
 -cdrom "$iso" -boot d -vga "${NOVA_QEMU_VGA:-std}" -display "${NOVA_DISPLAY:-gtk}" \
 -nic user,model=virtio-net-pci -serial "file:$ROOT/dist/qemu-serial.log" \
 -monitor "unix:$run/monitor.sock,server=on,wait=off" \
 -name 'Nova OS 0.1 — UEFI live test'
