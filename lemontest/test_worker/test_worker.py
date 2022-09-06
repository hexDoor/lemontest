from classes.test_worker import AbstractWorker
from pathlib import Path

import tempfile
import shutil
import sys
import os
import time

# This should be executed as a new process via multiprocessing (fork)
class TestWorker(AbstractWorker):
    parameters = None
    worker_root = None

    def __init__(self, **parameters):
        self.parameters = parameters
        try:
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

    def setup(self):
        # spawn container
        pass

    def support_execute(self, cmd):
        pass

    def execute(self, test):
        # TODO: execute the test
        time.sleep(1)
        pass

    def cleanup(self):
        # delete container
        # cleanup temp root
        if self.worker_root:
            shutil.rmtree(self.worker_root)


def pool_worker_test(worker_id):
    worker = TestWorker(worker_isolate_network=True, debug=False)
    worker.setup()
    #worker.support_execute(["ls", "-l"])
    #worker.support_execute(["cat", f"/proc/{os.getpid()}/setgroups"])
    worker.support_execute(["echo", f"pid: {os.getpid()} - worker: {worker_id}"])
    #worker.support_execute(["cat", f"/proc/{os.getpid()}/uid_map"])
    #worker.support_execute(["cat", f"/proc/{os.getpid()}/gid_map"])
    #worker.support_execute(["getpcaps", f"{os.getpid()}"])
    #worker.support_execute("id")
    #worker.support_execute(["capsh", "--print"])
    #worker.support_execute(["cat", "/etc/shadow"])
    #worker.support_execute(["cat", "/etc/subgid"])
    #worker.support_execute(["cat", f"/proc/{os.getpid()}/status"])
    #worker.support_execute(["cat", "README.md"])
    worker.cleanup()


if __name__ == '__main__':
    pool_worker_test(1)