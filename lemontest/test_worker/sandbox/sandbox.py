#
# sandbox
# some ideas inspired by https://github.com/shubham1172/pocket
# container config and PID1 inspired by https://github.com/balabit/furnace
#
from functools import reduce
from pathlib import Path
from collections import namedtuple

import uuid
import os

from .util import libc, fs
# A tuple can be to specify a different mount point in the
# sandbox 

class Sandbox:
    debug = False
    root_dir = None
    sandbox_id = None
    isolate_networking = None
    ro_mounts = None
    rw_mounts = None
    sandbox_pid1_manager = None

    def __init__(self, root_dir: Path, **parameters):
        self.debug = parameters["debug"]
        self.root_dir = root_dir.resolve()
        self.sandbox_id = str(uuid.uuid4())
        self.isolate_networking = parameters["worker_isolate_network"]

        # load mountables
        self.ro_mounts = parameters.get("sandbox_read_only_mount_base", [])
        self.ro_mounts += parameters.get("sandbox_read_only_mount", [])

        self.rw_mounts = parameters.get("sandbox_read_write_mount", [])
        self.rw_mounts += [self.root_dir]

        if self.debug:
            print(f"creating a new sandbox ({self.sandbox_id})")

        # TODO: setup system for proper BindMounts
        self.sandbox_pid1_manager = PID1Manager(self.root_dir, self.isolate_networking, [])

        # FIXME: rely on delegated cgroups v2 when support matures
        # with new python management libraries
        # existing libraries (cgroups, cgroupspy etc.) only handle
        # cgroups v1 which does not support rootless delegation

        # FIXME: consider systemd transient cgroups v2 scopes
        # see: https://manpages.ubuntu.com/manpages/bionic/man1/systemd-run.1.html

        # mount the file system
        # TODO: move to PID1
        if self.debug:
            print(f"Creating new file system")
        fs.setup_fs(root_dir)

    def run(self, cmd):
        pass

    def delete(self):
        pass


class PID1Manager:
    root_dir = None
    pid = None

    def __init__(self, root_dir, isolate_networking, bind_mounts):
        pass

    def start(self):
        pass
        libc.unshare(libc.CLONE_NEWPID)

        self.pid = os.fork()
        


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
        print(f"test_worker - unshare_user: uid: {os.getuid()} - gid: {os.getgid()}")

    # unshare user namespace and mount namespace
    libc.unshare(libc.CLONE_NEWUSER | libc.CLONE_NEWNS)

    # write uid & gid mapping
    if debug:
        print(f"test_worker - unshare_user: writing uidmap = '{uidmap}' => '{uidmapfile}'")
        print(f"test_worker - unshare_user: writing setgroups = 'deny' => '{setgroupsfile}'")
        print(f"test_worker - unshare_user: writing gidmap = '{gidmap}' => '{gidmapfile}'")

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
        print(f"test_worker - unshare_user: new uid = {os.getuid()} | new gid = {os.getgid()}")


# inspired by https://github.com/PexMor/unshare and Andrew Taylor's experiments
# also inspired by my friend ralismark
# https://github.com/ralismark/nix-appimage/blob/main/apprun.c
# because unshare(2) can't automatically map the root user :(
def unshare_process(isolate_networking: bool, debug: bool):
    if debug:
        print("test_worker - unshare_process: setting up unshare")
    unshare_user(debug)

    # unshare
    unshare_flags = [libc.CLONE_NEWCGROUP, libc.CLONE_NEWUTS, libc.CLONE_NEWIPC, libc.CLONE_NEWPID]
    if isolate_networking:
        unshare_flags.append(libc.CLONE_NEWNET)
    libc.unshare(reduce(lambda x, y: x|y, unshare_flags))

    # if i unshare PID namespace, the next subprocess must be the PID1 manager (everything needs to fork/execute off this)
    # perhaps run this when actually executing the test such that when it's done, it nicely exits?

    if debug:
        print(f"test_worker - unshare_process: done")


if __name__ == '__main__':
    pass