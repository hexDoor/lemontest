#
# Pure Python PID 1 handler
# inspired by https://github.com/balabit/furnace/
#

from functools import reduce
from pathlib import Path

import signal
import os
import stat

from . import libc
from .config import CONTAINER_MOUNTS, CONTAINER_ISOLATE_NETWORK_MOUNTS, CONTAINER_ISOLATE_NETWORK_BIND_MOUNTS, CONTAINER_DEVICE_NODES, BindMount

class PID1:
    def __init__(self, root_dir, isolate_networking, debug, bind_mounts):
        self.root_dir = Path(root_dir).resolve()
        self.isolate_networking = isolate_networking
        self.debug = debug
        self.bind_mounts = self.convert_bind_mounts_parameter(bind_mounts)
        self.old_root = os.open("/", os.O_PATH) # i'm going to regret having an open fd to root
        # but it's necessary for proper cleanup
    
    @classmethod
    def convert_bind_mounts_parameter(cls, bind_mounts):
        result = []
        for source, destination, read_only in bind_mounts:
            source = Path(source)
            destination = Path(destination)
            if destination.is_absolute():
                destination = destination.relative_to("/")
            result.append(BindMount(source, destination, read_only))
        return result

    def enable_zombie_reaping(self):
        # We are pid 1, so we have to take care of orphaned processes
        # We could SIG_IGN any SIGCHLD signals (which is the default)
        # However, explicitly providing SIG_IGN would inform the kernel
        # that we won't be wait'ing on any subprocesses and that the kernel
        # should remove subprocesses automatically from the pid table.
        # Unfortunately, that means we won't be able to get any exit codes
        # if we continue with this.
        # As such, we have to go with SIG_DFL in order to get the exit codes we need
        #signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)

    @classmethod
    def create_mount_target(cls, source, destination, is_device_node=False):
        if source.is_file() or is_device_node:
            if destination.is_symlink():
                destination.unlink()
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.touch()
        else:
            destination.mkdir(parents=True, exist_ok=True)

    def create_bind_mounts(self):
        # in the event network isolation is disabled we must bind mount /sys
        # see: https://lore.kernel.org/lkml/87ha2nyi3y.fsf@x220.int.ebiederm.org/
        if self.isolate_networking:
            self.bind_mounts += CONTAINER_ISOLATE_NETWORK_BIND_MOUNTS
        for source, relative_destination, read_only in self.bind_mounts:
            # check if the source actually exists (Issue picked up in Arch with missing /lib32)
            if not source.exists():
                if self.debug > 1:
                    print(f"WARNING: BindMount Skipped - '{source}' does not exist")
                continue

            destination = self.root_dir.joinpath(relative_destination)
            self.create_mount_target(source, destination)
            if self.debug > 1:
                print(f"Bind Mounting BindMount({source}, {relative_destination}, {read_only})")
            libc.mount(source, destination, None, libc.MS_BIND | libc.MS_REC , None)
            if read_only:
                # "Read-only bind mounts" are actually an illusion, a special feature of the kernel,
                # which is why we have to make the bind mount read-only in a separate call.
                # See https://lwn.net/Articles/281157/
                flags = libc.MS_REMOUNT | libc.MS_BIND | libc.MS_REC | libc.MS_RDONLY
                libc.mount(Path(), destination, None, flags, None)

    def setup_root_mount(self):
        # SLAVE means that mount events will get inside the container, but
        # mounting something inside will not leak out.
        # Use PRIVATE to not let outside events propagate in
        libc.mount(Path("none"), Path("/"), None, libc.MS_REC | libc.MS_SLAVE, None)
        if not libc.is_mount_point(self.root_dir):
            libc.mount(self.root_dir, self.root_dir, None, libc.MS_BIND, None)
        self.create_bind_mounts()
        old_root_dir = self.root_dir.joinpath('old_root')
        old_root_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(str(self.root_dir))
        libc.pivot_root(Path('.'), Path('old_root'))
        os.chroot('.')

    def mount_defaults(self):
        MOUNTS = CONTAINER_MOUNTS
        if self.isolate_networking:
            MOUNTS += CONTAINER_ISOLATE_NETWORK_MOUNTS
        for m in MOUNTS:
            options = None
            if m.options:
                options = ",".join(m.options)
            m.destination.mkdir(parents=True, exist_ok=True)
            if self.debug > 1:
                print(f"Mounting {m}")
            libc.mount(m.source, m.destination, m.type, m.flags, options)

    # keeping this in the event that mknod becomes available in user namespaces
    # in the meantime, the only possibility is to bind mount from the host machine
    def create_device_node(self, name, major, minor, mode, *, is_block_device=False):
        if is_block_device:
            device_type = stat.S_IFBLK
        else:
            device_type = stat.S_IFCHR
        nodepath = Path("/dev", name)
        # FIXME: This won't work as mknod requires superuser (not possible even with unshare)
        os.mknod(str(nodepath), mode=device_type, device=os.makedev(major, minor))
        # A separate chmod is necessary, because mknod (undocumentedly) takes umask into account when creating
        nodepath.chmod(mode=mode)

    def bind_device_node(self, source, destination, readonly):
        # at this point, root is mounted as /old_root
        src_nodepath = Path("/old_root/dev", source)
        dst_nodepath = Path("/dev", destination)
        # check if the source actually exists (Issue picked up in Arch with missing /lib32)
        if not src_nodepath.exists():
            if self.debug > 1:
                print(f"WARNING: BindMount Skipped - '{src_nodepath}' does not exist")
            return

        self.create_mount_target(src_nodepath, dst_nodepath, True)
        if self.debug > 1:
            print(f"Device Bind Mounting BindMount({src_nodepath}, {dst_nodepath}, {readonly})")
        libc.mount(src_nodepath, dst_nodepath, None, libc.MS_BIND | libc.MS_REC , None)
        if readonly:
            # "Read-only bind mounts" are actually an illusion, a special feature of the kernel,
            # which is why we have to make the bind mount read-only in a separate call.
            # See https://lwn.net/Articles/281157/
            flags = libc.MS_REMOUNT | libc.MS_BIND | libc.MS_REC | libc.MS_RDONLY
            libc.mount(Path(), dst_nodepath, None, flags, None)

    def create_default_dev_nodes(self):
        for d in CONTAINER_DEVICE_NODES:
            #self.create_device_node(have args here)
            self.bind_device_node(d.source, d.destination, d.readonly)

    def umount_old_root(self):
        libc.umount2('/old_root', libc.MNT_DETACH)
        os.rmdir('/old_root')

    def umount_default_dev_nodes(self):
        for d in CONTAINER_DEVICE_NODES:
            dst_nodepath = Path("/dev", d.destination)
            libc.umount2(dst_nodepath, libc.MNT_DETACH)
            # device nodes in /dev are files not directories
            os.remove(dst_nodepath)

    def umount_defaults(self):
        MOUNTS = CONTAINER_MOUNTS
        if self.isolate_networking:
            MOUNTS += CONTAINER_ISOLATE_NETWORK_MOUNTS
        for m in MOUNTS:
            libc.umount2(m.destination, libc.MNT_DETACH)
            os.rmdir(m.destination)
            pass

    def umount_bind_mounts(self):
        for _, relative_destination, _ in self.bind_mounts:
            # skip unmounting if destination doesn't exist
            # everything should be relative to root
            destination = Path("/").joinpath(relative_destination)
            if not destination.exists():
                if self.debug > 1:
                    print(f"WARNING: Unmount BindMount Skipped - '{destination}' does not exist")
                continue
            libc.umount2(destination, libc.MNT_DETACH)
            os.rmdir(destination)
    
    def umount_all(self):
        self.umount_default_dev_nodes()
        self.umount_defaults()
        self.umount_bind_mounts()

    def run(self):
        self.enable_zombie_reaping()
        unshare_process(self.isolate_networking)
        self.setup_root_mount()
        self.mount_defaults()
        self.create_default_dev_nodes()
        self.umount_old_root()

    def exit(self):
        # umount all for cleanup
        self.umount_all()

        # chroot back to default
        os.chdir(self.old_root)
        os.chroot('.')


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

def unshare_user(debug: int):
    # uid & gid mapping
    uid = os.getuid()
    gid = os.getgid()

    uidmapfile = f"/proc/self/uid_map"
    gidmapfile = f"/proc/self/gid_map"
    setgroupsfile = f"/proc/self/setgroups"
    uidmap = f"0 {uid} 1"
    gidmap = f"0 {gid} 1"

    if debug > 2:
        print(f"pid1 - unshare_user: uid: {os.getuid()} - gid: {os.getgid()}")

    # unshare user namespace
    libc.unshare(libc.CLONE_NEWUSER)

    # write uid & gid mapping
    if debug > 2:
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

    if debug > 2:
        print(f"pid1 - unshare_user: new uid = {os.getuid()} | new gid = {os.getgid()}")
