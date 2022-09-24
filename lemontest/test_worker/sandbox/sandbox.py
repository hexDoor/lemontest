#
# sandbox
# some ideas inspired by https://github.com/shubham1172/pocket
# container config and PID1 inspired by https://github.com/balabit/furnace
#
from pathlib import Path
from tempfile import mkdtemp

import uuid
import os
import subprocess
import time

from .util import libc, pid1
# A tuple can be to specify a different mount point in the
# sandbox 

class Sandbox:
    debug = False
    root_dir = None
    sandbox_id = None
    isolate_networking = None
    ro_mounts = None
    rw_mounts = None
    pid1_manager = None

    def __init__(self, root_dir: Path, **parameters):
        self.debug = parameters["debug"]
        self.root_dir = root_dir.resolve()
        self.sandbox_id = str(uuid.uuid4())
        self.isolate_networking = parameters.get("worker_isolate_network", True)

        # load mountables
        self.ro_mounts = parameters.get("sandbox_read_only_mount_base", [])
        self.ro_mounts += parameters.get("sandbox_read_only_mount", [])

        self.rw_mounts = parameters.get("sandbox_read_write_mount", [])
        self.rw_mounts += [self.root_dir]

        # TODO: translate mountables to bind mounts

        if self.debug:
            print(f"creating a new sandbox ({self.sandbox_id})")

        # TODO: setup system for proper BindMounts
        self.pid1_manager = PID1Manager(self.root_dir, self.isolate_networking, [], self.debug)

        # FIXME: rely on delegated cgroups v2 when support matures
        # with new python management libraries
        # existing libraries (cgroups, cgroupspy etc.) only handle
        # cgroups v1 which does not support rootless delegation

        # FIXME: consider systemd transient cgroups v2 scopes
        # see: https://manpages.ubuntu.com/manpages/bionic/man1/systemd-run.1.html

    def __enter__(self):
        self.pid1_manager.start() 

    def __exit__(self, exc_type, exc_value, traceback):
        if traceback:
            print("fuck")
        pass


class PID1Manager:
    root_dir = None
    isolate_networking = None
    bind_mounts = None
    debug = None
    pid = None
    pid1_class = None

    def __init__(self, root_dir, isolate_networking, bind_mounts, debug):
        self.root_dir = root_dir
        self.isolate_networking = isolate_networking
        self.bind_mounts = bind_mounts
        self.debug = debug

    def start(self):
        # unshare user namepsace here
        # can only unshare NEWPID once root user has been established
        # through namespaces
        # unfortunately, this needs to be here
        pid1.unshare_user(self.debug)

        # unshare the PID namespace at this point such that we can initialise a
        # pure-python PID 1
        libc.unshare(libc.CLONE_NEWPID)

        # fork python interpreter into child process to be PID 1
        self.pid = os.fork()
        
        # child process (PID 1)
        if self.pid == 0:
            # instantiate and execute PID1 setup as everything
            # from now on spawns from this process
            self.pid1_class = pid1.PID1(self.isolate_networking, self.debug)
        # wait then kill parent process which doesn't have pid 1
        # child process is PID1 so we're safe as all control gets inherited back
        else:
            # don't execute any exit handlers
            os._exit(0)


if __name__ == '__main__':
    with Sandbox(Path(mkdtemp()), debug=True) as sandbox:
        print(os.getpid())
        subprocess.run("id")
        print(os.getpid())
        subprocess.run(["ls", "-al", "/home/postgres"])
        print(os.getpid())
        subprocess.run(["touch", "/home/postgres/test"])