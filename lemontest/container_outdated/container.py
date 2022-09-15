#
# Isolates the current Python runtime and any subprocesses.
# AKA Containerise the current process/program and anything
# that is executed from the containerised current Python runtime
#
# I wish this could be a container context but most thoughts so far is
# that it requires root perms on the machine
# perhaps in the future, this can be re-written for rootless contexts
#

import os
import pwd

from functools import reduce

from .libc import unshare, CLONE_NEWNS, CLONE_NEWCGROUP, CLONE_NEWUTS, CLONE_NEWIPC, CLONE_NEWPID, CLONE_NEWUSER, CLONE_NEWNET


# path to tini process (PID 1 init binary)
TINI_PATH = os.path.join(os.path.dirname(__file__), 'tini')


def unshare_user(debug: bool):
    # uid & gid mapping
    uid = os.getuid()
    gid = os.getgid()

    # get subordinate uid and gid
    # considered using with but this might reduce the amount of unnecessary work
    # TODO: is this even necesssary?
    """
    account = pwd.getpwuid(os.getuid()).pw_name
    subuid_range = None
    subgid_range = None
    try:
        subuid_f = open("/etc/subuid", "r")
        subgid_f = open("/etc/subgid", "r")

        # get subuid range
        # translation for
        # grep -E "^z5208931:" /etc/subuid | cut -d: -f2- | tr ':' ' ' | sed 1q
        for line in subuid_f:
            if str(uid) in line or account in line:
                subuid_range = line.rstrip().split(":")[1:]
                break
        if debug:
            print(f"subuid range: {subuid_range}")

        # get subgid range
        # translation for
        # grep -E "^z5208931:" /etc/subgid | cut -d: -f2- | tr ':' ' ' | sed 1q
        for line in subgid_f:
            if str(gid) in line or account in line:
                subgid_range = line.rstrip().split(":")[1:]
                break
        if debug:
            print(f"subgid range: {subgid_range}")
    except Exception as err:
        raise err
    finally:
        if subuid_f:
            subuid_f.close()
        if subgid_f:
            subgid_f.close()
    #subuidmap = f"1 {' '.join(subuid_range)}"
    #subgidmap = f"1 {' '.join(subgid_range)}"
    """

    uidmapfile = f"/proc/self/uid_map"
    gidmapfile = f"/proc/self/gid_map"
    setgroupsfile = f"/proc/self/setgroups"
    uidmap = f"0 {uid} 1"
    gidmap = f"0 {gid} 1"

    if debug:
        print(f"test_worker - unshare_user: uid: {os.getuid()} - gid: {os.getgid()}")

    # unshare user namespace and mount namespace
    unshare(CLONE_NEWUSER | CLONE_NEWNS)

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
    unshare_flags = [CLONE_NEWCGROUP, CLONE_NEWUTS, CLONE_NEWIPC, CLONE_NEWPID]
    if isolate_networking:
        unshare_flags.append(CLONE_NEWNET)
    unshare(reduce(lambda x, y: x|y, unshare_flags))

    # if i unshare PID namespace, the next subprocess must be the PID1 manager (everything needs to fork/execute off this)
    # perhaps run this when actually executing the test such that when it's done, it nicely exits?

    if debug:
        print(f"test_worker - unshare_process: done")