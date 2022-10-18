from classes.test import AbstractTest
from .subprocess_with_resource_limits import run

from typing import List

from termcolor import colored as termcolor_colored
from collections import defaultdict
from pathlib import Path

import codecs
import io
import os
import sys
import shlex
import subprocess
import glob

class Test(AbstractTest):
    # predefined
    debug = None
    autotest_dir = None
    canonical_translator = None
    command = None
    files = None
    expected_stdout = None
    expected_stderr = None
    label = None
    parameters = None
    program = None
    stdin = None

    # runtime
    colored = None
    test_files = None
    stdout = None
    stderr = None
    explanation = None
    test_passed = False

    def __init__(self, autotest_dir, **parameters):
        self.debug = parameters["debug"]
        self.autotest_dir = autotest_dir

        # FIXME implement UNICODE handling
        # ignore all characters but those specified
        if parameters.get("compare_only_characters", ""):
            mapping = dict.fromkeys([chr(v) for v in range(0, 256)], None)
            if self.debug:
                print("compare_only_characters", parameters["compare_only_characters"])
            for c in parameters["compare_only_characters"] + "\n":
                mapping.pop(c, None)
        else:
            mapping = dict.fromkeys(parameters["ignore_characters"], None)
        self.canonical_translator = "".maketrans(mapping)
        
        self.command = parameters["command"]
        self.files = parameters["files"]
        self.expected_stdout = parameters["expected_stdout"]
        self.expected_stderr = parameters["expected_stderr"]
        self.label = parameters["label"]
        self.parameters = parameters
        self.program = parameters["program"]
        self.stdin = parameters["stdin"]

        self.colored = (
            termcolor_colored if parameters["colorize_output"] else lambda x, *a, **kw: x
        )
        self.test_files = None
        self.stdout = None
        self.stderr = None
        self.explanation = None
        self.test_passed = None


    def __str__(self):
        return f"Test({self.label}, {self.program}, {self.command})"

    # preprocess is a critical section
    # ensure this via a mutex lock
    def preprocess(self, file_dir: Path = None):
        # preprocess fail reasons
        description = f"Test {self.label} ({self.parameters['description']}) - "
        not_run_description = description + self.colored("could not be run")

        # file_dir is set if code to be run is within another directory
        # most like "/shared" if used in default state
        old_dir = os.getcwd()
        if file_dir:
            os.chdir(file_dir)
        try:
            glob_lists = [glob.glob(g) for g in self.files]
            self.test_files = [item for sublist in glob_lists for item in sublist]

            # run pre-compile checker and commands
            if not self.run_pre_compile_checkers():
                self.explanation = f"{not_run_description} because {self.colored('check failed')}"
                self.test_passed = False
                return False

            # TODO: run compile
            #subprocess.run(["ls", "-l"])
            #raise Exception("kek")
            return True
        except:
            self.test_passed = False
            return False # return fail status
        finally:
            if file_dir:
                os.chdir(old_dir)

        # TODO: symlink or copy files to test root

    def run_test(self, compile_command: str = ""):
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
        pass

    # TODO: add in legacy postprocessing
    def postprocess(self):
        # TODO: Failed test reasoning processing here
        self.test_passed = True
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
        on error, place stdout of script into test stdout
        return False iff any checker fails, True otherwise
        """
        for checker in self.parameters["checkers"]:
            if not checker:
                continue
            for filename in self.test_files:
                output = io.StringIO()
                if not run_support_command(
                    checker,
                    file=output,
                    arguments=[filename],
                    debug=self.debug
                ):
                    self.stdout = output.getvalue()
                    output.close()
                    return False
                output.close()

        pre_compile_command = self.parameters["pre_compile_command"]
        if pre_compile_command:
            output = io.StringIO()
            if not run_support_command(
                pre_compile_command,
                file=output,
                debug=self.debug
            ):
                self.stdout = output.getvalue()
                output.close()
                return False
            output.close()

        return True

    def params(self):
        return self.parameters

    def passed(self):
        return self.test_passed

def run_support_command(
    command: List[str],
    file=sys.stdout,
    arguments: List[str] = None,
    unlink: str = None,
    debug: bool = False,
) -> bool:
    """
    run support command, shell used iff command is a string
    command is not resource-limited, unlike tests
    if unlink is set, it is removed iff it is a symlink, before the command is run
    return True if command has 0 exit status, False otherwise
    """
    arguments = arguments or []
    if isinstance(command, str):
        cmd = command + " " + " ".join(arguments)
    else:
        cmd = command + arguments

    if unlink and os.path.exists(unlink) and os.path.islink(unlink):
        os.unlink(unlink)

    try:        
        p = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            input="",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            check=False,
        )
        file.write(p.stdout)
        result = p.returncode == 0
        return result
    except Exception as err:
        file.write(str(err))
        return False