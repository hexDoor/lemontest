from classes.test_scheduler import AbstractScheduler
from classes.test import AbstractTest
from test_worker.test_worker import TestWorker
from util.util import die, lambda_function, atexit_exc_decorator, SIGINT_MESSAGE
from util.fs import copy_files_to_directory
from util.subprocess import run_support_command

# typing
from argparse import Namespace
from typing import Dict, Any, List

# apply pool patch
import util.istarmap
from multiprocessing import Lock, set_start_method, get_context
from termcolor import colored as termcolor_colored
from pathlib import Path
from contextlib import contextmanager

import tqdm
import glob
import tempfile
import shutil
import atexit
import os
import io
import getpass
import signal
import sys

"""
import logging
logger = log_to_stderr()
logger.setLevel(SUBDEBUG)
"""

class TestScheduler(AbstractScheduler):
    args = None
    parameters = None
    debug = False
    shared_dir = None
    cleanup_run = False # need this to prevent cleanup running twice
    abort_global_cleanup = False

    def __init__(self, args: Namespace, parameters: Dict[str, Any]):
        self.args = args
        self.parameters = parameters
        self.debug = parameters["debug"]
        self.shared_dir = Path(tempfile.mkdtemp())
        atexit.register(lambda: shutil.rmtree(self.shared_dir))
        self.colored = (
            termcolor_colored
            if parameters["colorize_output"]
            else lambda_function
        )
        try:
            # catch any interrupt signals as a KeyboardInterrupt exception
            signal.signal(signal.SIGINT, scheduler_handler)
            # cleanup worker pool at exit (fixes issue with lemontest exiting without fully terminating processes)
            # this function is run during atexit so having a decorator to catch any exceptions will format accordingly
            atexit.register(atexit_exc_decorator(self.cleanup, self.debug))
        except Exception as err:
            die(err)

    def __str__(self):
        pass

    def schedule(self, tests: List[AbstractTest]) -> List[AbstractTest]:
        # check there are tests available to run
        if not tests:
            die(f"autotest not available for {self.args.exercise}")
        if not self.args.labels:
            die("nothing to test")

        # copy required files (student submission + test provided)
        # into a known temp directory from scheduler
        copy_files_to_directory(self.shared_dir, self.parameters, self.args)

        # check tests to ensure we have all files in the shared_dir to execute tests, otherwise die with missing files
        req_files_set = set.intersection(
            *[set(test.params()["files"]) for test in tests]
        )
        # FIXME: root_dir argument is only available in python 3.10
        # CSE at time of writing is on version 3.9 => have to do things the old fashioned way
        orig_dir = os.getcwd()
        os.chdir(self.shared_dir)
        missing_files = [f for f in req_files_set if not glob.glob(f)] # glob.glob(f, root_dir=self.shared_dir)
        if missing_files:
            die(f"Unable to run tests because these files were missing: {self.colored(' '.join(missing_files), 'red')}")
        os.chdir(orig_dir)

        # ask for any user provided parameters here (done after setup to minimise effort when forgetting to supply a file)
        # FIXME: try to find a better way to update all the tests nicely
        if self.global_user_environment_vars():
            for test in tests:
                test.set_param("environment", self.parameters["environment"])

        # run any overarching support setup commands here
        self.global_setup_command()

        # generate expected output if set
        for test in tests:
            test.set_param("generate_output", True if self.args.generate_expected_output != "no" else False)
            # override any checkers, so expected output can be generated from solutions with non-permitted features
            test.set_param("checkers", [])

        # process tests to be run
        tests = [(test, self.shared_dir, self.parameters) for test in tests]

        # schedule tests for execution and show progress
        # super cursed but it looks nice
        test_res = []
        pass_count = 0
        fail_count = 0
        count = 0

        try:
            # set the fork start method
            set_start_method("forkserver")
            # spawn Lock for test preprocessing shared directory access
            pLock = Lock()
            with get_context("forkserver").Pool(initializer=test_worker_init, initargs=(pLock,), processes=self.parameters["worker_count"], maxtasksperchild=1) as pool:
                pbar = tqdm.tqdm(pool.istarmap(test_worker, tests, chunksize=1), total=len(tests), unit=" test", disable=None)
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
        except KeyboardInterrupt:
            die(SIGINT_MESSAGE)
        except Exception as e:
            if self.debug:
                raise e
            else:
                die("There was an internal error with lemontest (unless you pressed ctrl+c or tried to kill autotest) but the error has been suppressed unless debug mode is enabled.")


        # return results
        return test_res

    def cleanup(self) -> None:
        # early exit if cleanup run
        if self.cleanup_run:
            return
        # run overarching cleanup support command
        # unless aborted
        if not self.abort_global_cleanup:
            self.global_clean_command()
        self.cleanup_run = True

    def global_setup_command(self):
        orig_dir = os.getcwd()
        os.chdir(self.shared_dir)
        # run global_setup_command within shared directory
        global_setup_command = self.parameters["global_setup_command"]
        # if custom envs are added, should update setup environ as well
        env = self.parameters["environment"]
        if global_setup_command:
            stdout = io.StringIO()
            retcode = run_support_command(
                global_setup_command,
                stdout=stdout,
                stderr=stdout,
                debug=self.debug,
                environ=env if env != os.environ else os.environ
            )
            if retcode != 0:
                explanation = stdout.getvalue()
                stdout.close()
                if retcode != 1:
                    self.abort_global_cleanup = True
                die(explanation)
            if self.debug:
                print(f"global_setup_command: '{global_setup_command}' return code: {retcode}")
                print(stdout.getvalue())
            stdout.close()
        os.chdir(orig_dir)

    def global_clean_command(self):
        orig_dir = os.getcwd()
        os.chdir(self.shared_dir)
        # run global_clean_command within shared directory
        global_clean_command = self.parameters["global_clean_command"]
        # if custom envs are added, should update setup environ as well
        env = self.parameters["environment"]
        if global_clean_command:
            stdout = io.StringIO()
            retcode = run_support_command(
                global_clean_command,
                stdout=stdout,
                stderr=stdout,
                debug=self.debug,
                environ=env if env != os.environ else os.environ
            )
            if retcode != 0:
                explanation = stdout.getvalue()
                stdout.close()
                die(explanation)
            if self.debug:
                print(f"global_clean_command: '{global_clean_command}' return code: {retcode}")
                print(stdout.getvalue())
            stdout.close()
        os.chdir(orig_dir)

    def global_user_environment_vars(self):
        # NOTE: could probably combine the two functions but want to keep things separate just in case
        environment = self.parameters["environment"]
        change_flag = False
        # load visible environment variable values
        for key in self.parameters["global_user_environment_vars"]:
            if self.debug:
                print(f"attempting to read visible env var '{key}'")
            if key in environment.keys():
                die(f"{key} already exists in provided environment")
            try:
                value = input(f"Enter value for environment variable '{key}':")
                environment.update({key: value})
                change_flag = True
            except EOFError:
                die(f"no input or EOF was given as the value for '{key}'")
            except Exception as err:
                die(f"critical error when giving value to environment variable '{key}' - {err}")

        # load hidden environment variable values
        for key in self.parameters["global_user_protected_environment_vars"]:
            if self.debug:
                print(f"attempting to read hidden env var '{key}'")
            if key in environment.keys():
                die(f"{key} already exists in provided environment")
            try:
                value = getpass.getpass(f"Enter value for environment variable '{key}' - (Input is Hidden):")
                environment.update({key: value})
                change_flag = True
            except EOFError:
                die(f"no input or EOF was given as the value for '{key}'")
            except Exception as err:
                die(f"critical error when giving value to environment variable '{key}' - {err}")

        # replace old environment
        if change_flag:
            self.parameters["environment"] = environment
        return change_flag

def scheduler_handler(signum, frame):
    raise KeyboardInterrupt(SIGINT_MESSAGE)


@contextmanager
def disable_exception_traceback():
    """
    All traceback information is suppressed and only the exception type and value are printed
    """
    default_value = getattr(sys, "tracebacklimit", 1000)  # `1000` is a Python's default value
    sys.tracebacklimit = 0
    yield
    sys.tracebacklimit = default_value  # revert changes


def test_worker_handler(signum, frame):
    with disable_exception_traceback():
        raise KeyboardInterrupt(SIGINT_MESSAGE) from None


def test_worker_self_terminate(signum, frame):
    raise TimeoutError()


# setup a global variable to inherit a global lock for the test preprocessing
# see: test_worker to see why this is absolutely necessary
# we can't use multiprocessing.Manager because that will break if we
# isolate networking within the sandbox (more common than not)
def test_worker_init(lock: Lock) -> None:
    global pLock
    pLock = lock
    signal.signal(signal.SIGINT, test_worker_handler)
    # automatically close myself if running for over a day (sometimes seems to happen on big servers)
    signal.signal(signal.SIGALRM, test_worker_self_terminate)
    signal.alarm(86400)


# initalise worker and execute task
def test_worker(test: AbstractTest, shared_dir: Path, parameters) -> AbstractTest:
    try:
        worker = TestWorker(shared_dir, **parameters)
        worker.setup()
        res = worker.execute(test, pLock) #pLock available from Pool initializer (global var)
        worker.cleanup()
        return res
    except TimeoutError:
        print(f"I am possibly a Zombie process (pid: {os.getpid()}) as I've existed for 24 hours running Test {test.label}. I am going to self terminate now.")
        test.mark_timeout()
        return test


if __name__ == '__main__':
    parameters = {'worker_count': 3, 'debug': True}
    test_scheduler = TestScheduler(**parameters)
    test_scheduler.schedule([1,2,3,4,5]) # change to tests
