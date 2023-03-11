from classes.reporter import AbstractReporter
from classes.test import AbstractTest

from termcolor import colored as termcolor_colored
from util.util import lambda_function, Tee
from reporter.util.upload import upload_results_http

# typing
from argparse import Namespace
from typing import Dict, Any, List

import tempfile
import atexit
import sys

class Reporter(AbstractReporter):
    args = None
    parameters = None
    debug = None
    upload_url = None
    colored = None
    log = None
    failed_count = 0
    not_run_count = 0
    seen_errors = {}

    def __init__(self, args: Namespace, parameters: Dict[str, Any]):
        self.args = args
        self.parameters = parameters
        self.debug = parameters["debug"]
        self.upload_url = parameters["upload_url"]
        self.colored = (
            termcolor_colored
            if parameters["colorize_output"]
            else lambda_function
        )
        # determine need for log file and setup
        if self.upload_url:
            self.log = tempfile.TemporaryFile(mode="w+")
            atexit.register(lambda: self.log.close())
            self.log = Tee(self.log)
        else:
            self.log = sys.stdout

    def generate_report(self, tests: List[AbstractTest]):
        # TODO: send tests to output module (prettier output) if set
        # i really don't like this personally but getting "same as test blah" requires this
        # same for not_run_tests
        for test in tests:
            if not test.passed():
                print(test.explanation(self.seen_errors), file=self.log)
                if not test.run_successful():
                    self.not_run_count += 1
                else:
                    self.failed_count += 1
            else:
                print(test, file=self.log)
        pass_str = self.colored(f"{len(tests) - self.failed_count - self.not_run_count} tests passed", "green")
        fail_str = self.colored(f"{self.failed_count} tests failed", "red" if self.failed_count else "green") # i hate this but it's necessary for output parity
        if self.not_run_count:
            # two spaces before tests could not be run for some reason
            print(f"{pass_str} {fail_str}  {self.not_run_count} tests could not be run", file=self.log)
        else:
            print(f"{pass_str} {fail_str}", file=self.log)

        if self.upload_url:
            upload_results_http(tests, self.parameters, self.args, self.log)

    def get_exit_code(self):
        return 1 if self.failed_count + self.not_run_count else 0
