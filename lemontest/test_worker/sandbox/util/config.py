# 

from collections import namedtuple
from pathlib import Path

from .libc import MS_NOSUID, MS_NOEXEC, MS_NODEV, MS_RDONLY, MS_REC, MS_STRICTATIME

Mount = namedtuple('Mount', ['destination', 'type', 'source', 'flags', 'options'])
DeviceNode = namedtuple('DeviceNode', ['name', 'major', 'minor'])
BindMount = namedtuple('BindMount', ['source', 'destination', 'readonly'])

DEFAULT_PATH = ["/usr/sbin", "/usr/bin", "/sbin", "/bin"]

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

# default devices that are necessary/commonly used
CONTAINER_DEVICE_NODES = [
    
    BindMount(
        source="null",
        destination="null",
        readonly=False
    ),
    BindMount(
        source="zero",
        destination="zero",
        readonly=False
    ),
    BindMount(
        source="full",
        destination="full",
        readonly=False
    ),
    BindMount(
        source="random",
        destination="random",
        readonly=False
    ),
    BindMount(
        source="urandom",
        destination="urandom",
        readonly=False
    ),
]
"""
CONTAINER_DEVICE_NODES = [
    DeviceNode(
        name="null",
        major=1,
        minor=3,
    ),
    #DeviceNode(
    #    name="zero",
    #    major=1,
    #    minor=5,
    #),
    #DeviceNode(
    #    name="full",
    #    major=1,
    #    minor=7,
    #),
    #DeviceNode(
    #    name="tty",
    #    major=5,
    #    minor=0,
    #),
    #DeviceNode(
    #    name="random",
    #    major=1,
    #    minor=8,
    #),
    #DeviceNode(
    #    name="urandom",
    #    major=1,
    #    minor=9,
    #),
]
"""