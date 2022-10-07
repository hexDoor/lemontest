# 

from collections import namedtuple
from pathlib import Path

from .libc import MS_NOSUID, MS_NOEXEC, MS_NODEV, MS_RDONLY, MS_REC, MS_STRICTATIME

Mount = namedtuple('Mount', ['destination', 'type', 'source', 'flags', 'options'])
BindMount = namedtuple('BindMount', ['source', 'destination', 'readonly'])


# /tmp, /proc, /sys and /dev are always mounted
# directly read-write in the sandbox
CONTAINER_MOUNTS = [
    Mount(
        destination=Path("/tmp"),
        type="tmpfs",
        source="tmp",
        flags=MS_NOSUID | MS_STRICTATIME,
        options=[
            "mode=1777",
        ],
    ),
    Mount(
        destination=Path("/proc"),
        type="proc",
        source="proc",
        flags=0,
        options=None,
    ),
    Mount(
        destination=Path("/dev"),
        type="tmpfs",
        source="tmpfs",
        flags=MS_NOSUID | MS_STRICTATIME,
        options=[
            "mode=755",
            "size=65536k",
        ],
    ),
    #Mount(
    #    destination=Path("/dev/pts"),
    #    type="devpts",
    #    source="devpts",
    #    flags=MS_NOSUID | MS_NOEXEC,
    #    options=[
    #        "newinstance",
    #        "ptmxmode=0666",
    #        "mode=0620",
    #        "gid=5",
    #    ],
    #),
    #Mount(
    #    destination=Path("/dev/shm"),
    #    type="tmpfs",
    #    source="shm",
    #    flags=MS_NOSUID | MS_NOEXEC | MS_NODEV,
    #    options=[
    #        "mode=1777",
    #        "size=65536k",
    #    ],
    #),
    #Mount(
    #    destination=Path("/dev/mqueue"),
    #    type="mqueue",
    #    source="mqueue",
    #    flags=MS_NOSUID | MS_NOEXEC | MS_NODEV,
    #    options=None,
    #),
    Mount(
        destination=Path("/sys"),
        type="sysfs",
        source="sysfs",
        flags=MS_NOSUID | MS_NOEXEC | MS_NODEV | MS_RDONLY,
        options=None,
    ),
]