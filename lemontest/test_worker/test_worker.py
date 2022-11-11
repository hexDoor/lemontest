from classes.test_worker import AbstractWorker
from classes.test import AbstractTest
from util.util import lambda_function
from pathlib import Path
from termcolor import colored as termcolor_colored
from multiprocessing import Lock

import tempfile
import shutil
import atexit

from .sandbox.sandbox import Sandbox, SHARED_DIR_DEST

# This should be executed as a new process via multiprocessing (fork)
class TestWorker(AbstractWorker):
    shared_dir = None
    parameters = None
    worker_root = None
    debug = None
    colored = None

    def __init__(self, shared_dir: Path, **parameters):
        self.shared_dir = shared_dir
        self.parameters = parameters
        self.worker_root = Path(tempfile.mkdtemp())
        atexit.register(lambda: shutil.rmtree(self.worker_root))
        self.debug = parameters["debug"]
        self.colored = (
            termcolor_colored
            if parameters["colorize_output"]
            else lambda_function
        )

    def __str__(self):
        info = {
            "shared_dir": self.shared_dir,
            "worker_root": self.worker_root
        }
        return str(info)

    def setup(self):
        pass

    def execute(self, test: AbstractTest, pLock: Lock):
        # this also allows us to cache on a shared binary resource
        # as such, we also consider test.preprocess() to be a critical section

        # rw bind in the scheduler temp directory (should allow caching between worker processes but must use lock)
        # available within Sandbox as "/shared" 
        # spawn sandbox runtime context
        with Sandbox(self.worker_root, self.shared_dir, **self.parameters) as sb:
            # run test preprocessing
            pLock.acquire()
            pStatus = test.preprocess(SHARED_DIR_DEST)
            pLock.release()
            if not pStatus:
                return test

            # execute test
            rStatus = test.run_test(SHARED_DIR_DEST)
            if not rStatus:
                return test

            # perform test postprocessing (output checking etc.)
            test.postprocess()

        # return processed test
        return test

    def cleanup(self):
        pass

if __name__ == '__main__':
    parameters = {'worker_count': 3, 'debug': True}
    worker = TestWorker(**parameters)
    worker.setup()
    worker.cleanup()