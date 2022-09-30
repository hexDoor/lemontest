from classes.test_worker import AbstractWorker
from classes.test import AbstractTest
from pathlib import Path
from termcolor import colored as termcolor_colored

import tempfile
import shutil
import os

from .sandbox.sandbox import Sandbox

# This should be executed as a new process via multiprocessing (fork)
class TestWorker(AbstractWorker):
    parameters = None
    worker_root = None
    debug = None
    colored = None

    def __init__(self, **parameters):
        self.parameters = parameters
        self.worker_root = Path(tempfile.mkdtemp())
        self.debug = parameters["debug"]
        self.colored = (
            termcolor_colored
            if parameters["colorize_output"]
            else lambda x, *a, **kw: x
        )

    def __str__(self):
        info = {
            "worker_root": self.worker_root
        }
        return str(info)

    def setup(self):
        # TODO: copy files to temp directory
        # TODO: run pre-compile
        # TODO: run compile
        
        pass

    def execute(self, test: AbstractTest):
        # spawn sandbox runtime context
        with Sandbox(self.worker_root, **self.parameters) as sb:
            test.preprocess()
            #test.run_test()
            print(test)
            test.postprocess()

        # return processed test
        return test

    def cleanup(self):
        # cleanup temp root
        if self.worker_root:
            shutil.rmtree(self.worker_root)

if __name__ == '__main__':
    parameters = {'worker_count': 3, 'debug': True}
    worker = TestWorker(**parameters)
    worker.setup()
    worker.cleanup()