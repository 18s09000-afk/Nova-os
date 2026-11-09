#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
python3 tests/check_config.py
shellcheck auto/config scripts/*.sh config/hooks/live/*.chroot
bash -n scripts/*.sh
# Exercise live-build itself outside the source tree.
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
cp -a auto config "$work/"
(cd "$work" && ./auto/config)
grep -q 'trixie' "$work/config/bootstrap"
grep -q 'grub-efi' "$work/config/binary"
# Resolve against the same archive areas as the ISO, independent of host APT sources.
mkdir -p "$work/lists/partial"
printf "%s\n" "deb https://deb.debian.org/debian trixie main contrib non-free non-free-firmware" "deb https://security.debian.org/debian-security trixie-security main contrib non-free non-free-firmware" > "$work/sources.list"
apt_options=(-o "Dir::Etc::sourcelist=$work/sources.list" -o "Dir::Etc::sourceparts=-" -o "Dir::State::lists=$work/lists" -o "APT::Sandbox::User=$(id -un)")
apt-get "${apt_options[@]}" update
packages=$(sed -e '/^#/d' -e '/^$/d' config/package-lists/nova.list.chroot)
# Intentional splitting: one package name per input line, validated above.
# shellcheck disable=SC2086
apt-get "${apt_options[@]}" --simulate install $packages > "$work/package-resolution.log"
mkdir -p dist
cp "$work/package-resolution.log" dist/package-resolution.log
printf 'Configuration, shell checks and package resolution: PASS\n'
