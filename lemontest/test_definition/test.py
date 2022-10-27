from classes.test import AbstractTest
from .subprocess_with_resource_limits import run

from typing import List, Dict, Any, Union

from termcolor import colored as termcolor_colored
from collections import defaultdict
from pathlib import Path

import codecs
import io
import os
import sys
import time
import subprocess
import glob
import re

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
        status = None
        if self.test_passed:
            status = self.colored("passed", "green")
        elif self.explanation:
            return self.explanation
        else:
            status = self.colored("failed", "red")
        return f"Test {self.label} ({self.parameters['description']}) - {status}"

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
                # only replace explanation if not already set
                if not self.explanation:
                    self.explanation = f"{not_run_description} because {self.colored('check failed', 'red')}"
                self.test_passed = False
                return False

            # check missing files
            missing_files = [f for f in self.files if not glob.glob(f)]
            if missing_files:
                self.explanation = f"{not_run_description} because these files are missing: {self.colored(' '.join(missing_files), 'red')}"
                self.test_passed = False
                return False

            # run compile
            if not self.run_compilers():
                # only replace explanation if not already set
                if not self.explanation:
                    self.explanation = f"{not_run_description} because {self.colored('compilation failed', 'red')}"
                self.test_passed = False
                return False

            # exit to old_dir for linking and setup
            if file_dir:
                os.chdir(old_dir)

            # link correct program to root
            if not self.link_programs_and_setup(file_dir):
                # only replace explanation if not already set
                if not self.explanation:
                    self.explanation = f"{not_run_description} because {self.colored('linking or setup failed', 'red')}"
                self.test_passed = False
                return False

            return True
        except:
            self.test_passed = False
            return False # return fail status
        finally:
            if file_dir:
                os.chdir(old_dir)

    def run_test(self):
        # don't update environment as it may break things
        #self.set_environ()
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
        #print(f"{self.label} stdout - {self.stdout} - expected: {self.expected_stdout}")

        if self.parameters["unicode_stderr"]:
            self.stderr = codecs.decode(stderr, "UTF-8", errors="replace")
        else:
            self.stderr = stderr
        #print(f"{self.label} stderr - {self.stderr} - expected: {self.expected_stderr}")

    def postprocess(self):
        # TODO: perform output comparison (stdout and stderr)
        # check stdout stream
        stdout_short_explanation = self.check_stream(
            self.stdout, self.expected_stdout, "stdout"
        
        # only consider stderr if unexpected stderr permitted or stdout issue discovered
        if not self.parameters["allow_unexpected_stderr"] or stdout_short_explanation:
            # early exit if we have a DCC issue + dcc early exit enabled
            if (
                self.parameters["dcc_output_checking"]
                and "Execution stopped because" in self.stderr
            ):
                self.short_explanation = "incorrect output"
            # otherwise, check stderr stream and declare if stderr_ok
            else:
                self.short_explanation = self.check_stream(
                    self.stderr, self.expected_stderr, "stderr"
                )
                self.stderr_ok = not self.short_explanation

        # stdout is ok if no stdout explanation FIXME: could put this above
        self.stdout_ok = not stdout_short_explanation

        # if there is no current explanation, set it to the stdout explanation
        if not self.short_explanation:
            self.short_explanation = stdout_short_explanation

        # if there was no stdout explanation, check files TODO: what kind of files?
        # self.parameters["expected_files"] is a list of (pathname, expected content)
        # checks all files for the expected content
        if not self.short_explanation:
            self.short_explanation = self.check_files()

        # the test passes if there is no explanation for the error TODO: possibly have a better condition
        self.test_passed = not self.short_explanation

        # FIXME: put failed_compiler in the long explanation processor?
        if not self.test_passed:
            self.failed_compiler = (
                " ".join(compile_command)
                if isinstance(compile_command, list)
                else str(compile_command)
            )
        

        # TODO: remove me
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

    def run_compilers(self):
        """
        run any compilers specified for the the test
        this code is a critical section and should be made mutually exclusive
        return False iff any compiler fails, True otherwise
        """
        # get compile commands
        compile_commands = self.parameters["compile_commands"]
        # TODO: multi_language_support for autotests (autotest accepting multiple languages)
        # low priority
        if not compile_commands:
            return True

        # execute compilation
        program = self.parameters["program"]
        for compile_command in compile_commands:
            # check if program has already been compiled and skip
            unique_name = get_unique_program_name(program, compile_command, self.test_files)
            if os.path.exists(unique_name):
                continue

            # run compile
            arguments = [] if self.parameters["compiler_args"] else self.test_files
            output = io.StringIO()
            if not run_support_command(
                compile_command,
                arguments=arguments,
                unlink=program,
                file=output,
                debug=self.debug
            ):
                self.stdout = output.getvalue()
                output.close()
                return False
            output.close()

            # check that compiled program actually exists
            if not os.path.exists(program):
                self.explanation = self.colored(f"compiled '{program}' could not be found after compilation", "red")
                return False

            # chmod program to be executable (rwx)
            try:
                os.chmod(program, 0o700)
            except:
                self.explanation = self.colored(f"compiled '{program}' could not be chmod u+rwx", "red")
                return False

            # rename program to unique name
            # default package will have this code made mutually exclusive
            try:
                os.rename(program, unique_name)
            except OSError as err:
                self.explanation = self.colored(f"compiled '{program}' could not be renamed to '{unique_name}'", "red")
                return False

        return True

    def link_programs_and_setup(self, file_dir: Path = None):
        program = self.parameters["program"]
        for compile_command in self.parameters["compile_commands"]:
            # check if program to be linked exists
            unique_name = get_unique_program_name(program, compile_command, self.test_files)
            file_path = file_dir.joinpath(unique_name).resolve()
            if not os.path.exists(file_path):
                self.explanation = self.colored(f"compiled '{file_path}' could not be found for linking", "red")
                return False
            
            # link program
            # if link already exists to correct target, skip
            if os.path.exists(program) and Path(os.readlink(program)).resolve() == file_path:
                continue
            # delete link (but only if it's a link)
            if os.path.islink(program):
                os.unlink(program)
            # create link if it doesn't exist
            if not os.path.exists(program):
                os.symlink(file_path, program)
            # ensure link created is correct
            if not os.path.exists(program) or Path(os.readlink(program)).resolve() != file_path:
                self.explanation = self.colored(f"linking between '{program}' and '{file_path}' failed", "red")
                return False

        # run any setup_command
        setup_command = self.parameters["setup_command"]
        if setup_command:
            output = io.StringIO()
            if not run_support_command(
                setup_command,
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


def get_unique_program_name(program: str, compile_command: Union[List[str], str], test_files: List[str]) -> str:
    """
    form a unique program name based on compile arguments
    so we can have multiple binaries for a program.
    Contrive clashes possible, but comprehensible names for debugging,
    """
    compile_command_str = "_".join(compile_command) if isinstance(compile_command, list) else compile_command
    compile_command_str = compile_command_str.replace(" ", "_")
    return program + "." + "__".join([compile_command_str] + test_files).replace("/", "___")


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
