# python wrapper around unshare libc syscalls
#

import ctypes
import logging

logger = logging.getLogger(__name__)

libc = ctypes.CDLL("libc.so.6", use_errno=True)

CLONE_NEWUSER = 0x10000000
CLONE_NEWNS = 0x00020000
CLONE_NEWCGROUP = 0x02000000
CLONE_NEWUTS = 0x04000000
CLONE_NEWIPC = 0x08000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000

def unshare(flags):
    if libc.unshare(flags) != 0:
        raise OSError(ctypes.get_errno(), "unshare failed")