from classes.test_worker import AbstractWorker
from functools import reduce
from pathlib import Path

import tempfile
import shutil
import sys
import os
import pwd
import subprocess

from container_outdated import container

# This should be executed as a new process via multiprocessing (fork)
# the os.fork() call will allow us to work with unshare
# At the current time, there is no way to communicate with
class TestWorker(AbstractWorker):
    worker_root = None
    pid1_manager = None

    def __init__(self, **parameters):
        # containerise current process
        try:
            # isolate current process with unshare
            container.unshare_process(parameters["worker_isolate_network"], parameters["debug"])

            # setup and mount fakeroot
            self.worker_root = Path(tempfile.mkdtemp())
        except Exception as err:
            # TODO: figure out a way to tell the pool manager that this is fucked
            # and everything needs to be exit
            print(err)
            sys.exit(1)


    def __str__(self):
        info = {
            "worker_root": self.worker_root
        }
        return str(info)

    def setup(self, **parameters):
        pass

    def support_execute(self, cmd):
        print(f"support_exec: {os.getpid()}")
        return subprocess.run(cmd, shell=True).returncode


    def execute(self, test):
        pass

    def cleanup(self):
        # cleanup temp root
        if self.worker_root:
            shutil.rmtree(self.worker_root)


def pool_worker_test(worker_id):
    worker = TestWorker(worker_isolate_network=True, debug=False)
    worker.setup()
    pid = os.fork()
    if pid == 0:
        #worker.support_execute(["/proc/self/exe"])
        #worker.support_execute([container.TINI_PATH, "--", "pwd"])
        #worker.support_execute(["ls", "-l"])
        #worker.support_execute(["cat", f"/proc/{os.getpid()}/setgroups"])
        #worker.support_execute(["echo $$"])
        #worker.support_execute(["echo", f"pid: {os.getpid()} - worker: {worker_id} - subprocess pid: $$"])
        worker.support_execute([f"echo 'pid: {os.getpid()} - worker: {worker_id} - subprocess pid' $$"])
        #worker.support_execute(["cat", f"/proc/{os.getpid()}/uid_map"])
        #worker.support_execute(["cat", f"/proc/{os.getpid()}/gid_map"])
        #worker.support_execute(["getpcaps", f"{os.getpid()}"])
        worker.support_execute("id")
        #worker.support_execute(["capsh", "--print"])
        #worker.support_execute(["cat", "/etc/shadow"])
        #worker.support_execute(["cat", "/etc/subgid"])
        #worker.support_execute(["cat", f"/proc/{os.getpid()}/status"])
        #worker.support_execute(["cat", "README.md"])
    else:
        print(f"not child: {os.getpid()}")
        _, status = os.waitpid(pid, 0)
    worker.cleanup()


if __name__ == '__main__':
    from multiprocessing import Pool
    pool = Pool(4, maxtasksperchild=1)

    #pool.map(pool_worker_test, [1,2,3,4,5,6,7,8])
    pool.map(pool_worker_test, [1])
    pool.terminate()

    pool.close()