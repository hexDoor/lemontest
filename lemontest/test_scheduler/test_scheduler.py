from classes.test_scheduler import AbstractScheduler
from classes.test import AbstractTest
from test_worker.test_worker import TestWorker
from util.util import die
from util.fs import copy_files_to_directory

# typing
from argparse import Namespace
from typing import Dict, Any, List

# apply pool patch
import util.istarmap
from multiprocessing import set_start_method, Pool, Lock, log_to_stderr, SUBDEBUG
from termcolor import colored as termcolor_colored
from pathlib import Path

import tqdm
import glob
import tempfile
import shutil
import atexit

"""
import logging
logger = log_to_stderr()
logger.setLevel(SUBDEBUG)
"""

class TestScheduler(AbstractScheduler):
    args = None
    parameters = None
    shared_dir = None
    worker_pool = None

    def __init__(self, args: Namespace, parameters: Dict[str, Any]):
        self.args = args
        self.parameters = parameters
        self.shared_dir = Path(tempfile.mkdtemp())
        atexit.register(lambda: shutil.rmtree(self.shared_dir))
        self.colored = (
            termcolor_colored
            if parameters["colorize_output"]
            else lambda x, *a, **kw: x
        )
        try:
            # set the fork start method
            set_start_method('fork')
            # spawn Lock for test preprocessing shared directory access
            pLock = Lock()
            # spawn worker pool
            self.worker_pool = Pool(initializer=test_worker_init, initargs=(pLock,), processes=self.parameters["worker_count"], maxtasksperchild=1)
        except Exception as err:
            die(err)
        finally:
            # cleanup worker pool
            if self.worker_pool:
                self.worker_pool.terminate() # send SIGTERM to worker processes

    def __str__(self):
        pass

    def schedule(self, tests: List[AbstractTest]) -> List[AbstractTest]:
        # check there are tests available to run
        if not tests:
            die(f"autotest not available for {self.args.exercise}")
        if not self.args.labels:
            die("nothing to test")

        # process tests to be run
        tests = [(test, self.shared_dir, self.parameters) for test in tests]

        # FIXME: compile.sh and runtests.pl was executed here usually

        # check tests to ensure we have all files to execute tests, otherwise die with missing files
        req_files_set = set.intersection(
            *[set(test.params()["files"]) for (test, _, _) in tests]
        )
        missing_files = [f for f in req_files_set if not glob.glob(f)]
        if missing_files:
            die(f"Unable to run tests because these files were missing: {self.colored(' '.join(missing_files), 'red')}")

        # copy required files (student submission + test provided)
        # into a known temp directory from scheduler
        copy_files_to_directory(self.shared_dir, self.parameters, self.args)

        # schedule tests for execution and show progress
        # super cursed but it looks nice
        test_res = []
        pass_count = 0
        fail_count = 0
        count = 0
        pbar = tqdm.tqdm(self.worker_pool.istarmap(test_worker, tests, chunksize=1), total=len(tests), unit=" test")
        for res in pbar:
            if res.passed():
                pass_count += 1
            else:
                fail_count += 1
            total_desc = f"Running {len(tests)} tests"
            pass_desc = self.colored(f"{pass_count} tests passed", "green")
            fail_desc = self.colored(f"{fail_count} tests failed", "red")
            pbar.set_description(f"{total_desc} | {pass_desc} | {fail_desc}")
            test_res.append(res)
            count += 1
            if count == len(tests):
                pbar.set_description(f"Ran {len(tests)} tests | {pass_desc} | {fail_desc}")

        # terminate worker pool as work is done
        self.worker_pool.terminate()
        self.worker_pool.join() # this doesn't sometimes work with .close() so just terminate

        # reset worker_pool in case cleanup gets triggered by signal
        self.worker_pool = None

        # return results
        return test_res

    def cleanup(self) -> None:
        if self.worker_pool:
            self.worker_pool.terminate() # send SIGTERM to worker processes


# setup a global variable to inherit a global lock for the test preprocessing
# see: test_worker to see why this is absolutely necessary
# we can't use multiprocessing.Manager because that will break if we
# isolate networking within the sandbox (more common than not)
def test_worker_init(lock: Lock) -> None:
    global pLock
    pLock = lock


# initalise worker and execute task
def test_worker(test: AbstractTest, shared_dir: Path, parameters) -> AbstractTest:
    worker = TestWorker(shared_dir, **parameters)
    worker.setup()
    res = worker.execute(test, pLock) #pLock available from Pool initializer (global var)
    worker.cleanup()
    return res


if __name__ == '__main__':
    parameters = {'worker_count': 3, 'debug': True}
    test_scheduler = TestScheduler(**parameters)
    test_scheduler.schedule([1,2,3,4,5]) # change to tests