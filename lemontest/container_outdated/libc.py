# python wrapper around unshare libc syscalls
# inspired by furnace libc library https://github.com/balabit/furnace
#

UNSHARE_COMMAND = [
    "/usr/bin/unshare",
    "--cgroup",
    "--fork",
    "--ipc",
    "--map-root-user",
    "--mount",
    "--net",
    "--pid",
    "--user",
    "--time",
    "--uts",
]

import ctypes
from pathlib import Path

libc = ctypes.CDLL("libc.so.6", use_errno=True)

# unshare
CLONE_NEWUSER = 0x10000000
CLONE_NEWNS = 0x00020000
CLONE_NEWCGROUP = 0x02000000
CLONE_NEWUTS = 0x04000000
CLONE_NEWIPC = 0x08000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000

def unshare(flags: int):
    if libc.unshare(flags) != 0:
        raise OSError(ctypes.get_errno(), "unshare failed")


# mount
MS_RDONLY = 0x00000001
MS_NOSUID = 0x00000002
MS_NODEV = 0x00000004
MS_NOEXEC = 0x00000008
MS_REMOUNT = 0x00000020
MS_NOATIME = 0x00000400
MS_NODIRATIME = 0x00000800
MS_BIND = 0x00001000
MS_MOVE = 0x00002000
MS_REC = 0x00004000
MS_PRIVATE = 0x00040000
MS_SLAVE = 0x00080000
MS_SHARED = 0x00100000
MS_STRICTATIME = 0x01000000

def mount(source: Path, target: Path, fstype, flags, data):
    if fstype is not None:
        fstype = fstype.encode('utf-8')
    if data is not None:
        data = data.encode('utf-8')
    if libc.mount(str(source).encode('utf-8'), str(target).encode('utf-8'), fstype, flags, data) != 0:
        raise OSError(ctypes.get_errno(), "Mount failed")