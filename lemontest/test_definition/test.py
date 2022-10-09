from classes.test import AbstractTest
from .subprocess_with_resource_limits import run

from termcolor import colored as termcolor_colored
from collections import defaultdict
from pathlib import Path

import codecs
import time
import os
import shlex
import subprocess
import time

class Test(AbstractTest):
    autotest_dir = None
    canonical_translator = None
    command = None
    debug = None
    files = None
    expected_stdout = None
    expected_stderr = None
    explanation = None
    label = None
    parameters = None
    program = None
    stdin = None

    test_passed = False

    def __init__(self, autotest_dir, **parameters):
        debug = parameters["debug"]
        self.autotest_dir = autotest_dir

        # FIXME implement UNICODE handling
        # ignore all characters but those specified
        if parameters.get("compare_only_characters", ""):
            mapping = dict.fromkeys([chr(v) for v in range(0, 256)], None)
            if debug:
                print("compare_only_characters", parameters["compare_only_characters"])
            for c in parameters["compare_only_characters"] + "\n":
                mapping.pop(c, None)
        else:
            mapping = dict.fromkeys(parameters["ignore_characters"], None)
        self.canonical_translator = "".maketrans(mapping)
        
        self.command = parameters["command"]
        self.debug = parameters["debug"]
        self.files = parameters["files"]
        self.expected_stdout = parameters["expected_stdout"]
        self.expected_stderr = parameters["expected_stderr"]
        self.explanation = None
        self.label = parameters["label"]
        self.parameters = parameters
        self.program = parameters["program"]
        self.stdin = parameters["stdin"]

        self.test_passed = None

    def __str__(self):
        return f"Test({self.label}, {self.program}, {self.command})"

    # preprocess is a critical section
    # ensure this via a mutex lock
    def preprocess(self, file_dir: Path = None):
        # file_dir is set if code to be run is within another directory
        # most like "/shared" if used in default state
        if file_dir:
            os.chdir(file_dir)
        try:
            # TODO: run pre-compile checker (in progress)
            self.run_pre_compile_checkers()
            # TODO: run compile
            #subprocess.run(["ls", "-l"])
            #raise Exception("kek")
            return True
        except:
            self.test_passed = False
            return False # return fail status
        finally:
            if file_dir:
                os.chdir(file_dir)

    def run_test(self, compile_command=""):
        """
        if self.debug:
            print(
                f'run_test(compile_command="{compile_command}", command="{self.command}")\n'
            )

        self.set_environ()

        for attempt in range(3):
            if self.debug:
                print("run_test attempt", attempt)
            (stdout, stderr, self.returncode) = run(**self.parameters)
            if stdout or stderr or self.returncode == 0 or not self.expected_stdout:
                break
            if self.debug:
                print("run_test retry", (stdout, stderr, self.returncode))
            # ugly work-around for
            # weird termination with non-zero exit status seen on some CSE servers
            # ignore this execution and try again
            # TODO: try testing if we can remove this?
            time.sleep(1)

        if self.parameters["unicode_stdout"]:
            self.stdout = codecs.decode(stdout, "UTF-8", errors="replace")
        else:
            self.stdout = stdout

        if self.parameters["unicode_stderr"]:
            self.stderr = codecs.decode(stderr, "UTF-8", errors="replace")
        else:
            self.stderr = stderr
        """
        self.test_passed = True

    # TODO: add in legacy postprocessing
    def postprocess(self):
        pass

    # helper functions
    def set_environ(self):
        test_environ = self.parameters["environment"]
        if os.environ != test_environ:
            os.environ.clear()
            os.environ.update(test_environ)

    def run_pre_compile_checkers(self):
        """
        run any checkers specified for the files in the test
        plus any pre_compile_command
        if they haven't been run before
        return False iff any checker fails, True otherwise
        """
        for checker in self.parameters["checkers"]:
            if not checker:
                continue
        pass

    def params(self):
        return self.parameters

    def passed(self):
        return self.test_passed