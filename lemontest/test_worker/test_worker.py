from classes.test_worker import AbstractWorker
from classes.test import AbstractTest
from pathlib import Path

import tempfile
import shutil
import os
import time

from .sandbox.sandbox import Sandbox

# This should be executed as a new process via multiprocessing (fork)
class TestWorker(AbstractWorker):
    parameters = None
    worker_root = None

    def __init__(self, **parameters):
        self.parameters = parameters
        self.worker_root = Path(tempfile.mkdtemp())


    def __str__(self):
        info = {
            "worker_root": self.worker_root
        }
        return str(info)

    def setup(self):
        # do nothing as not needed but here to follow design
        pass

    def execute(self, test: AbstractTest):
        # spawn sandbox runtime context
        with Sandbox(self.worker_root, **self.parameters) as sb:
            # TODO: execute test in sandbox
            test.preprocess()
            time.sleep(2)
            test.label = test.label + "kek"
            #print(os.getpid())
            #subprocess.run("id")
            #test.run_test()
            #print("running test")
            #print(test)
            test.postprocess()

        # return processed test
        print(f"returning {test}")
        return test

    def cleanup(self):
        # cleanup temp root
        if self.worker_root:
            shutil.rmtree(self.worker_root)