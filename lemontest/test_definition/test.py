from classes.test import AbstractTest
from .subprocess_with_resource_limits import run
from .output_differences import compare_strings, report_difference, report_bit_differences, sanitize_string, insert_hex_slash_x, echo_command_for_string, check_bad_characters
from .defs import STDOUT, STDERR

from typing import List, Dict, Any, Union

from termcolor import colored as termcolor_colored
from pathlib import Path

import codecs
import io
import os
import sys
import time
import subprocess
import glob
import re
import copy

class Test(AbstractTest):
    # predefined
    debug = None
    autotest_dir = None
    canonical_translator = None
    command = None
    compile_commands = None
    files = None
    optional_files = None
    expected_stdout = None
    expected_stderr = None
    label = None
    parameters = None
    program = None
    stdin = None

    # runtime
    colored = None
    test_files = None
    individual_tests = None
    stdout = None
    stderr = None
    short_explanation = None
    long_explanation = None
    test_passed = False

    # runtime (process_long_explanation function specific)
    stdout_ok = True
    stderr_ok = True
    file_not_ok_path = None
    file_expected = None
    file_actual = None

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
        self.compile_commands = parameters["compile_commands"]
        self.files = parameters["files"]
        self.optional_files = parameters["optional_files"]
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
        self.individual_tests = None
        self.stdout = None
        self.stderr = None
        self.short_explanation = None
        self.long_explanation = None
        self.test_passed = None

    def __str__(self):
        # In the event the test isn't run before being printed
        if self.test_passed is None:
            return f"Test {self.label} ({self.parameters['description']}) - {self.colored('not tested', 'red')}"
        status = None
        if self.test_passed:
            status = self.colored("passed", "green")
        else:
            status = f"{self.colored('failed', 'red')} ({self.short_explanation})"
            if self.long_explanation:
                status += "\n"
                status += self.long_explanation
        return f"Test {self.label} ({self.parameters['description']}) - {status}"

    # preprocess is a critical section
    # ensure this via a mutex lock
    def preprocess(self, file_dir: Path):
        # preprocess fail reasons
        not_run_description = self.colored("could not be run")

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
                if not self.short_explanation:
                    self.short_explanation = f"{not_run_description} because {self.colored('check failed', 'red')}"
                self.test_passed = False
                return False

            # check and link missing files
            missing_files = [f for f in self.files if not glob.glob(f)]
            if missing_files:
                self.short_explanation = f"{not_run_description} because these files are missing: {self.colored(' '.join(missing_files), 'red')}"
                self.test_passed = False
                return False

            # run compile
            if not self.run_compilers():
                # only replace explanation if not already set
                if not self.short_explanation:
                    self.short_explanation = f"{not_run_description} because {self.colored('compilation failed', 'red')}"
                self.test_passed = False
                return False

            # exit to old_dir for submission
            if file_dir:
                os.chdir(old_dir)

            # link correct programs to root
            if not self.link_submission_files(file_dir):
                # only replace explanation if not already set
                if not self.short_explanation:
                    self.short_explanation = f"{not_run_description} because {self.colored('linking of submission files failed', 'red')}"
                self.test_passed = False
                return False

            return True
        except:
            self.test_passed = False
            return False # return fail status
        finally:
            if file_dir:
                os.chdir(old_dir)

    def run_test(self, file_dir: Path):
        """
        Required design break as each "test" isn't really it's own test as we have to execute
        one instance of a test per compiler command.
        I (Kyu-Sang) personally don't like this but to keep backwards compatability, this is necessary
        """
        self.individual_tests = []
        # will always execute once because of program should already exist at this point
        # (eg. shell files don't need compilation)
        for compile_command in self.compile_commands or [""]:
            # individual_test fail reason
            not_run_description = self.colored("could not be run")

            # link correct program to root if a compile command existed
            # or continue (program should already exist) eg. shell files
            if compile_command and not self.link_program(compile_command, file_dir):
                # only replace explanation if not already set
                if not self.short_explanation:
                    self.short_explanation = f"{not_run_description} because {self.colored('linking failed', 'red')}"
                self.test_passed = False
                return False

            # run setup of test
            if not self.setup_test():
                # only replace explanation if not already set
                if not self.short_explanation:
                    self.short_explanation = f"{not_run_description} because {self.colored('setup failed', 'red')}"
                self.test_passed = False
                return False
            
            individual_test = copy.copy(self) # shallow copy self
            if not compile_command:
                compile_command_str = ""
            elif isinstance(compile_command, list):
                compile_command_str = " ".join(compile_command)
            else:
                compile_command_str = compile_command
            if not self.parameters["compiler_args"]:
                compile_command_str += " " + " ".join(self.test_files)
            # execute test with specific compile_command
            # run in serial to minimise potential issues with sandboxing (complete autotest overhaul may be required for this)
            # TODO: consider running this in parallel with sandboxing but seems excessive for what will usually be one compile command
            #start = time.time()
            individual_test.run_individual_test(compile_command=compile_command_str)
            #end = time.time()
            #print(f"{self.label} {self.parameters['description']} {compile_command_str} - {end-start}")
            self.individual_tests.append(individual_test)

            # early exit if running into an obvious error
            # stderr_ok available from processing short_explanation (runtime class member)
            if not individual_test.stderr_ok and not self.parameters["allow_unexpected_stderr"]:
                break

        return True
    
    def run_individual_test(self, compile_command: Union[List[str], str] = ""):
        if self.debug:
            print(f'run_test(compile_command="{compile_command}", command="{self.command}")\n')

        # don't update environment as it may break things
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

        # checks for any issues in stdout or stderr and/or files
        self.process_short_explanation()
        # the test passes if there is no explanation for the error
        self.test_passed = not self.short_explanation

        # the compile_command for which the test failed upon
        if not self.test_passed:
            self.failed_compiler = (
                " ".join(compile_command)
                if isinstance(compile_command, list)
                else str(compile_command)
            )

        # NOTE: skip any long explanation processing till postprocessing and only do it if necessary

    def postprocess(self):
        # determine if we have passed all individual tests
        # then 
        failed_individual_tests = [it for it in self.individual_tests if not it.passed()]
        self.test_passed = not failed_individual_tests
        # early exit if we have passed all individual tests
        if self.test_passed:
            self.stdout = self.individual_tests[0].stdout
            self.stderr = self.individual_tests[0].stderr
            return

        # pick the best failed test to report
        # if we have errors then should be more informative than incorrect output except memory leaks
        if not failed_individual_tests[-1].stderr_ok and (
            not self.parameters["unicode_stderr"]
            or ("free not called" not in failed_individual_tests[-1].stderr)
        ):
            individual_test = failed_individual_tests[-1]
        else:
            individual_test = failed_individual_tests[0]

        self.stdout = individual_test.stdout
        self.stderr = individual_test.stderr
        self.short_explanation = individual_test.short_explanation
        self.long_explanation = individual_test.get_long_explanation()

    def params(self):
        return self.parameters

    def passed(self):
        return self.test_passed

    def explanation(self, previous_errors: Dict[str, Any]):
        # If test has passed, refer to __str__ function
        if self.test_passed is None or self.test_passed:
            return str(self)
        
        # check if error has been seen before and minimise error
        status = f"{self.colored('failed', 'red')} ({self.short_explanation})"
        if self.long_explanation:
            reduced_long_explanation = re.sub(r"0x[0-9a-f]+", "", self.long_explanation, flags=re.I)
            if reduced_long_explanation in previous_errors:
                status += f" - same as Test {previous_errors[reduced_long_explanation]}"
            else:
                status += "\n"
                status += self.long_explanation
            previous_errors.setdefault(reduced_long_explanation, self.label)
        return f"Test {self.label} ({self.parameters['description']}) - {status}"

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
                    self.long_explanation = output.getvalue()
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
                self.long_explanation = output.getvalue()
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
        compile_commands = self.compile_commands
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
                self.long_explanation = output.getvalue()
                output.close()
                return False
            output.close()

            # check that compiled program actually exists
            if not os.path.exists(program):
                self.short_explanation = self.colored(f"compiled '{program}' could not be found after compilation", "red")
                return False

            # chmod program to be executable (rwx)
            try:
                os.chmod(program, 0o700)
            except:
                self.short_explanation = self.colored(f"compiled '{program}' could not be chmod u+rwx", "red")
                return False

            # rename program to unique name
            # default package will have this code made mutually exclusive
            try:
                os.rename(program, unique_name)
            except OSError as err:
                self.short_explanation = self.colored(f"compiled '{program}' could not be renamed to '{unique_name}'", "red")
                return False

        return True

    def link_submission_files(self, file_dir: Path):
        # link submission files
        submission_files = self.files + self.optional_files
        # FIXME: Try to get this section put into a function
        for file in submission_files:
            file_path = file_dir.joinpath(file).resolve()
            # skip if missing file is optional otherwise find file for linking
            if not os.path.exists(file_path) and file in self.optional_files:
                continue
            elif not os.path.exists(file_path):
                self.short_explanation = self.colored(f"'{file_path}' could not be found for linking", "red")
                return False

            # if link already exists to correct target, skip
            if os.path.exists(file) and Path(os.readlink(file)).resolve() == file_path:
                continue
            # delete link (but only if it's a link)
            if os.path.islink(file):
                os.unlink(file)
            # create link if it doesn't exist
            if not os.path.exists(file):
                os.symlink(file_path, file)
            # ensure link created is correct
            if not os.path.exists(file) or Path(os.readlink(file)).resolve() != file_path:
                self.short_explanation = self.colored(f"linking between '{file}' and '{file_path}' failed", "red")
                return False

        return True

    def link_program(self, compile_command: Union[List[str], str], file_dir: Path):
        # link compiled program
        program = self.parameters["program"]
        # check if program to be linked exists
        unique_name = get_unique_program_name(program, compile_command, self.test_files)
        file_path = file_dir.joinpath(unique_name).resolve()
        if not os.path.exists(file_path):
            self.short_explanation = self.colored(f"compiled '{file_path}' could not be found for linking", "red")
            return False

        # if link already exists to correct target, skip
        if os.path.exists(program) and Path(os.readlink(program)).resolve() == file_path:
            return True
        # delete link (but only if it's a link)
        if os.path.islink(program):
            os.unlink(program)
        # create link if it doesn't exist
        if not os.path.exists(program):
            os.symlink(file_path, program)
        # ensure link created is correct
        if not os.path.exists(program) or Path(os.readlink(program)).resolve() != file_path:
            self.short_explanation = self.colored(f"linking between '{program}' and '{file_path}' failed", "red")
            return False

        return True

    def setup_test(self):
        # run any setup_command
        setup_command = self.parameters["setup_command"]
        if setup_command:
            output = io.StringIO()
            if not run_support_command(
                setup_command,
                file=output,
                debug=self.debug
            ):
                self.long_explanation = output.getvalue()
                output.close()
                return False
            output.close()

        return True
    
    def check_stream(self, actual, expected, name):
        if self.debug:
            print("name:", name)
            print("actual:", actual[0:256] if actual else "")
            print("expected:", expected[0:256] if expected else "")
        if actual:
            if expected:
                # Handling non-unicode IO
                if type(actual) in (bytearray, bytes) or type(expected) in (
                    bytearray,
                    bytes,
                ):
                    if actual == bytearray(expected):
                        return None
                    else:
                        return "Your non-unicode output is not correct"
                # handling unicode input
                if compare_strings(actual, expected, self.canonical_translator, self.parameters):
                    return None
                else:
                    return "Incorrect " + name
            else:
                if name == STDERR:
                    return "errors"
                elif name == STDOUT:
                    return name + " produced when none expected"
                else:
                    return name + " should be empty and was not"
        else:
            if expected:
                if name.lower().startswith("file"):
                    return f"File {name} is empty"
                else:
                    return f"No {name} produced"
            else:
                return None

    def check_files(self):
        for (pathname, expected_contents) in self.parameters["expected_files"].items():
            try:
                if self.parameters["unicode_files"]:
                    with open(pathname, encoding="UTF-8", errors="replace") as f:
                        actual_contents = f.read()
                else:
                    with open(pathname, mode="rb") as f:
                        actual_contents = f.read()
            except IOError:
                self.long_explanation = f"Your program was expected to create a file named '{pathname}' and did not\n"
                actual_contents = ""
            short_explanation = self.check_stream(
                actual_contents, expected_contents, f"file: {pathname}"
            )
            if short_explanation:
                self.file_not_ok_path = pathname
                self.file_expected = expected_contents
                self.file_actual = actual_contents
                return short_explanation

    def process_short_explanation(self):
        # perform output comparison (stdout and stderr)
        # check stdout stream
        stdout_short_explanation = self.check_stream(
            self.stdout, self.expected_stdout, STDOUT
        )
        # stdout is ok if no stdout explanation
        self.stdout_ok = not stdout_short_explanation

        # only consider stderr if unexpected stderr permitted or stdout issue discovered
        if not self.parameters["allow_unexpected_stderr"] or not self.stdout_ok:
            # early exit if we have a DCC issue + dcc early exit enabled
            if (
                self.parameters["dcc_output_checking"]
                and "Execution stopped because" in self.stderr
            ):
                self.short_explanation = "incorrect output"
            # otherwise, check stderr stream and declare if stderr_ok
            else:
                self.short_explanation = self.check_stream(
                    self.stderr, self.expected_stderr, STDERR
                )
                self.stderr_ok = not self.short_explanation

        # if there is no current explanation, set it to the stdout explanation
        # in most cases, stderr provides better short explanation
        if not self.short_explanation:
            self.short_explanation = stdout_short_explanation

        # if there was no stdout explanation, check files TODO: what kind of files?
        # self.parameters["expected_files"] is a list of (pathname, expected content)
        # checks all files for the expected content
        if not self.short_explanation:
            self.short_explanation = self.check_files()

    def stdin_file_name(self):
        return ""
        # fix-me for reproduce commands we should generate a filename in some circumstances
        if not self.stdin_file:
            return self.stdin_file
        if self.stdin_file[0] == "/":
            return self.stdin_file
        path = os.path.realpath(self.autotest_dir + "/" + self.stdin_file)
        path = re.sub(r"/tmp_amd/\w+/export/\w+/\d/(\w+)", r"/home/\1", path)
        return path

    # Get Long Explanation of what went wrong in the test
    # output differences and how to recreate the test
    def get_long_explanation(self):
        if self.debug:
            print(
                "get_long_explanation() short_explanation=",
                self.short_explanation,
                "long_explanation=",
                self.long_explanation,
                "stderr_ok=",
                self.stderr_ok,
                "expected_stderr=",
                self.expected_stderr,
            )

        # if a long_explanation already exists, do not override
        if self.long_explanation:
            return self.long_explanation

        self.long_explanation = ""
        # report differences in stderr
        if not self.stderr_ok:
            # if stderr output was expected -> report differences
            if self.expected_stderr:
                if self.parameters["unicode_stderr"]:
                    self.long_explanation += report_difference(STDERR, self.expected_stderr, self.stderr, self.canonical_translator, self.debug, self.parameters)
                else:
                    self.long_explanation = f"You had 0x{self.stderr.hex()} as stderr. "
                    self.long_explanation += f"You should have 0x{self.expected_stderr.hex()}\n\n"
                    expected_bits = self.expected_stderr
                    actual_bits = self.stderr
                    self.long_explanation += report_bit_differences(expected_bits, actual_bits)
            # if we are to check DCC errors and a DCC error has been seen
            # FIXME: Possible a better way to determine a DCC error other than looking a specific "Execution stopped because" string?
            elif self.parameters["dcc_output_checking"] and "Execution stopped because" in self.stderr:
                n_output_lines = len(self.stdout.splitlines())
                self.long_explanation += f"Your program produced these {n_output_lines} lines of output before it was terminated:\n"
                self.long_explanation += self.colored(sanitize_string(self.stdout, **self.parameters), "cyan")
                self.long_explanation += self.stderr + "\n"
            else:
                errors = sanitize_string(self.stderr, leave_tabs=True, leave_colorization=True, **self.parameters)
                if "\x1b" not in self.long_explanation:
                    errors = self.colored(errors, "red")
                if "Error too much output" in self.stderr:
                    errors += f"Your program produced these {len(self.stdout)} bytes of output before it was terminated:\n"
                    errors += self.colored(sanitize_string(self.stdout, **self.parameters), "yellow")
                if self.stdout_ok and self.expected_stdout:
                    self.long_explanation = "Your program's output was correct but errors occurred:\n"
                    self.long_explanation += errors
                    self.long_explanation += "Apart from the above errors, your program's output was correct.\n"
                else:
                    self.long_explanation = "Your program produced these errors:\n"
                    self.long_explanation += errors
        if not self.stdout_ok and (self.parameters["show_stdout_if_errors"] or self.stderr_ok):
            # If we don't have unicode in out stdout, we should check for bad characters
            bad_characters = False
            if self.parameters["unicode_stdout"]:
                bad_characters = check_bad_characters(self.colored, self.stdout, expected=self.expected_stdout)
            if bad_characters:
                self.long_explanation += bad_characters
                self.parameters["show_diff"] = False
            # report output differences in a easily readable manner
            # if we don't have unicode input.
            if self.parameters["unicode_stdout"]:
                self.long_explanation += report_difference(STDOUT, self.expected_stdout, self.stdout, self.canonical_translator, self.debug, self.parameters)
            else:
                self.long_explanation = f"You had 0x{self.stdout.hex()} as stdout. "
                self.long_explanation += f"You should have 0x{self.expected_stdout.hex()}\n\n"
                expected_bits = self.expected_stdout
                actual_bits = self.stdout
                self.long_explanation += report_bit_differences(expected_bits, actual_bits)

        if self.stdout_ok and self.stderr_ok and self.file_not_ok_path:
            if self.parameters["unicode_files"]:
                self.long_explanation = report_difference(self.file_not_ok_path, self.file_expected, self.file_actual, self.canonical_translator, self.debug, self.parameters)
            else:
                self.long_explanation = "Your non-unicode files had incorrect output\n"
                self.long_explanation += f"File {self.file_not_ok_path} had the following error:\n"
                self.long_explanation += f"expected: 0x{self.file_expected.hex()} "
                self.long_explanation += f"actual: 0x{self.file_actual.hex()}\n"
                expected_bits = self.file_expected
                actual_bits = self.file_actual
                self.long_explanation += report_bit_differences(expected_bits, actual_bits)

        std_input = self.stdin
        unicode_stdin = self.parameters["unicode_stdin"]

        # we don't want to consider newlines when dealing with non-unicode output
        if self.parameters["unicode_stdin"]:
            n_input_lines = std_input.count("\n")

        if self.parameters["show_stdin"]:
            if unicode_stdin and std_input and n_input_lines < 32:
                self.long_explanation += f"\nThe input for this test was:\n{self.colored(std_input, 'yellow')}\n"
                if std_input[-1] != "\n" and "\n" in std_input[:-2]:
                    self.long_explanation += "Note: last character in above input is not '\\n'\n\n"
            elif (not unicode_stdin) and std_input:
                self.long_explanation += f"\nThe input for this test was:\n{self.colored('0x' + std_input.hex(), 'yellow')}\n"

        if self.parameters["show_reproduce_command"]:
            indent = "  "
            self.long_explanation += "You can reproduce this test by executing these commands:\n"
            if self.failed_compiler:
                self.long_explanation += self.colored(indent + self.failed_compiler + "\n", "blue")
            command = " ".join(self.command) if isinstance(self.command, list) else self.command
            if std_input:
                if unicode_stdin:
                    echo_command = echo_command_for_string(std_input)
                else:
                    echo_command = "echo -n" + "'" + insert_hex_slash_x(std_input[1:].hex())

                if not self.stdin_file_name() or len(echo_command) < 128:
                    if "shell" in self.parameters and (";" in command or "&" in command or "|" in command):
                        command = "(" + command + ")"
                    command = f"{echo_command} | {command}"
                else:
                    command += " <" + self.stdin_file_name()
                command = indent + command
            else:
                if "shell" in self.parameters and not self.parameters.get("no_replace_semicolon_reproduce_command", ""):
                    command = re.sub(r"\s*;\s*", "\n" + indent, command)
                command = indent + command

            self.long_explanation += self.colored(command + "\n", "blue")
        
        return self.long_explanation

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
