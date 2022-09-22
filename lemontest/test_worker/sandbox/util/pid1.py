from functools import reduce

import signal
import os

from . import libc

class PID1:
    def __init__(self, isolate_networking, debug):
        self.enable_zombie_reaping()
        unshare_process(isolate_networking)

    def enable_zombie_reaping(self):
        # We are pid 1, so we have to take care of orphaned processes
        # Interestingly, SIG_IGN is the default handler for SIGCHLD,
        # but this way we signal to the kernel that we will not call waitpid
        # and get rid of zombies automatically
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

# inspired by https://github.com/PexMor/unshare and Andrew Taylor's experiments
# also inspired by my friend ralismark
# https://github.com/ralismark/nix-appimage/blob/main/apprun.c
# because unshare(2) can't automatically map the root user :(
def unshare_process(isolate_networking: bool):
    # unshare
    unshare_flags = [libc.CLONE_NEWCGROUP, libc.CLONE_NEWUTS, libc.CLONE_NEWIPC, libc.CLONE_NEWNS]
    if isolate_networking:
        unshare_flags.append(libc.CLONE_NEWNET)
    libc.unshare(reduce(lambda x, y: x|y, unshare_flags))

def unshare_user(debug: bool):
    # uid & gid mapping
    uid = os.getuid()
    gid = os.getgid()

    uidmapfile = f"/proc/self/uid_map"
    gidmapfile = f"/proc/self/gid_map"
    setgroupsfile = f"/proc/self/setgroups"
    uidmap = f"0 {uid} 1"
    gidmap = f"0 {gid} 1"

    if debug:
        print(f"pid1 - unshare_user: uid: {os.getuid()} - gid: {os.getgid()}")

    # unshare user namespace
    libc.unshare(libc.CLONE_NEWUSER)

    # write uid & gid mapping
    if debug:
        print(f"pid1 - unshare_user: writing uidmap = '{uidmap}' => '{uidmapfile}'")
        print(f"pid1 - unshare_user: writing setgroups = 'deny' => '{setgroupsfile}'")
        print(f"pid1 - unshare_user: writing gidmap = '{gidmap}' => '{gidmapfile}'")

    # user_namespaces(7)
    # The data written to uid_map (gid_map) must consist of a single line that
    # maps the writing process's effective user ID (group ID) in the parent
    # user namespace to a user ID (group ID) in the user namespace.
    with open(uidmapfile, "w") as uidmap_f:
        uidmap_f.write(uidmap)

    # user_namespaces(7)
    # In the case of gid_map, use of the setgroups(2) system call must first
    # be denied by writing "deny" to the /proc/[pid]/setgroups file (see
    # below) before writing to gid_map.
    with open(setgroupsfile, "w") as setgroups_f:
        setgroups_f.write("deny")    
    with open(gidmapfile, "w") as gidmap_f:
        gidmap_f.write(gidmap)

    if debug:
        print(f"pid1 - unshare_user: new uid = {os.getuid()} | new gid = {os.getgid()}")
