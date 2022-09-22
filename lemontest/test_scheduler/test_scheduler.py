from classes.test_scheduler import AbstractScheduler
from test_worker.test_worker import TestWorker

# apply pool patch
import util.istarmap
from multiprocessing import Pool, log_to_stderr, SUBDEBUG 

import sys
import tqdm

"""
import logging
logger = log_to_stderr()
logger.setLevel(SUBDEBUG)
"""

class TestScheduler(AbstractScheduler):
    parameters = None
    worker_pool = None

    def __init__(self, **parameters):
        self.parameters = parameters
        try:
            # spawn worker pool
            self.worker_pool = Pool(self.parameters["worker_count"], maxtasksperchild=1)
        except Exception as err:
            # cleanup worker pool
            if self.worker_pool:
                self.worker_pool.terminate() # send SIGTERM to worker processes
            print(err)
            sys.exit(1)

    def __str__(self):
        pass

    def schedule(self, tests):
        tests = [(test, self.parameters) for test in tests]
        print("HELP1")
        for test, _ in tests:
            print(test)
        # schedule tests for execution and show progress
        test_res = list(tqdm.tqdm(self.worker_pool.istarmap(test_worker, tests, chunksize=1), total=len(tests), desc=f"Running {len(tests)} tests:", unit=" tests"))
        
        # terminate worker pool as work is done
        self.worker_pool.terminate()
        self.worker_pool.join() # this doesn't sometimes work

        # reset worker_pool in case cleanup gets triggered by signal
        self.worker_pool = None
        print("HELP2")
        for test in test_res:
            print(test)

        # return results
        return test_res

    def cleanup(self):
        if self.worker_pool:
            self.worker_pool.terminate() # send SIGTERM to worker processes


# initalise worker and execute task
def test_worker(test, parameters):
    worker = TestWorker(**parameters)
    worker.setup()
    res = worker.execute(test)
    worker.cleanup()
    return res


if __name__ == '__main__':
    parameters = {'worker_count': 3, 'debug': True}
    test_scheduler = TestScheduler(**parameters)
    test_scheduler.schedule([1,2,3,4,5]) # change to tests