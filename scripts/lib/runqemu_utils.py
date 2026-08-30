#!/usr/bin/env python3
#
# Helpers shared by runqemu and NFS-rootfs preparation tools.
#
# SPDX-License-Identifier: GPL-2.0-only

"""Extract and export rootfs tarballs for NFS booting."""

import os
import subprocess
import sys


class RunQemuRootfsError(Exception):
    """Raised when an NFS rootfs cannot be prepared or exported."""


def native_environment():
    """Return the qemu-helper-native environment set by oe-find-native-sysroot."""
    command = '''
        helper=$(command -v oe-find-native-sysroot) || exit 127
        . "$helper" qemu-helper-native >/dev/null
        env -0
        printf 'PSEUDO=%s\\0OECORE_NATIVE_SYSROOT=%s\\0' "$PSEUDO" "$OECORE_NATIVE_SYSROOT"
    '''
    result = subprocess.run(['bash', '-c', command], capture_output=True)
    if result.returncode:
        if result.returncode == 127:
            raise RunQemuRootfsError(
                'Unable to find the oe-find-native-sysroot script.\n'
                'Did you forget to source your build system environment setup script?')
        raise RunQemuRootfsError(
            result.stderr.decode(errors='replace').strip() or
            'Unable to set up the qemu-helper-native sysroot')

    environment = {}
    for entry in result.stdout.split(b'\0'):
        if b'=' in entry:
            key, value = entry.split(b'=', 1)
            environment[key.decode()] = value.decode()
    return environment


def _tar_options(rootfs_tarball):
    if rootfs_tarball.endswith('.tar.xz'):
        return ['--numeric-owner', '-xJf']
    if rootfs_tarball.endswith('.tar.bz2'):
        return ['--numeric-owner', '-xjf']
    if rootfs_tarball.endswith('.tar.gz'):
        return ['--numeric-owner', '-xzf']
    if rootfs_tarball.endswith('.tar.zst'):
        return ['--numeric-owner', '--zstd', '-xf']
    if rootfs_tarball.endswith('.tar'):
        return ['--numeric-owner', '-xf']
    raise RunQemuRootfsError(
        'Unable to determine sdk tarball format\n'
        'Accepted types: .tar / .tar.gz / .tar.bz2 / .tar.xz / .tar.zst')


def pseudo_state_dir(rootfs_dir):
    """Return the pseudo database location associated with an extracted rootfs."""
    rootfs_dir = os.path.realpath(rootfs_dir)
    return os.path.join(os.path.dirname(rootfs_dir),
                        os.path.basename(rootfs_dir) + '.pseudo_state')


def extract_sdk_rootfs(rootfs_tarball, rootfs_dir):
    """Extract a rootfs tarball under pseudo and return its absolute directory."""
    if not os.path.exists(rootfs_tarball):
        raise RunQemuRootfsError("sdk tarball '%s' does not exist" % rootfs_tarball)

    rootfs_tarball = os.path.realpath(rootfs_tarball)
    rootfs_dir = os.path.realpath(rootfs_dir)
    tar_options = _tar_options(rootfs_tarball)
    state_dir = pseudo_state_dir(rootfs_dir)
    debug_image = '-dbg' in os.path.basename(rootfs_tarball)

    if os.path.exists(state_dir) and not debug_image:
        raise RunQemuRootfsError(
            '%s already exists!\n'
            'Please delete the rootfs tree and pseudo directory manually\n'
            'if this is really what you want.' % state_dir)

    os.makedirs(rootfs_dir, exist_ok=True)
    os.makedirs(state_dir, exist_ok=True)
    open(os.path.join(state_dir, 'pseudo.pid'), 'a').close()

    environment = native_environment()
    environment['PSEUDO_LOCALSTATEDIR'] = state_dir
    environment['PSEUDO_INCLUDE_PATHS'] = rootfs_dir
    pseudo = environment.get('PSEUDO')
    native_sysroot = environment.get('OECORE_NATIVE_SYSROOT')
    if not pseudo or not native_sysroot:
        raise RunQemuRootfsError('qemu-helper-native did not provide pseudo')

    command = [pseudo, '-P', os.path.join(native_sysroot, 'usr'), 'tar', '-C', rootfs_dir]
    command.extend(tar_options)
    command.append(rootfs_tarball)
    print('Extracting rootfs tarball using pseudo...')
    print(' '.join(command))
    try:
        subprocess.run(command, env=environment, check=True)
    except subprocess.CalledProcessError as exc:
        raise RunQemuRootfsError('Failed to extract rootfs tarball') from exc

    if len(os.listdir(rootfs_dir)) < 4:
        print("Warning: I don't see many files in %s" % rootfs_dir)
        print('Please double-check the extraction worked as intended')
    else:
        print('SDK image successfully extracted to %s' % rootfs_dir)
    return rootfs_dir


def extract_sdk_main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print('Usage: %s <image-tarball> <extract-dir>' % sys.argv[0])
        return 1
    try:
        extract_sdk_rootfs(*argv)
    except RunQemuRootfsError as exc:
        print('Error: %s' % exc)
        return 1
    return 0
