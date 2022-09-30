# run a single test
#
# This code needs extensive rewriting.
# Much of the code can be moved to parameter_descriptions.py

import codecs, os, re, shlex, subprocess, time
from termcolor import colored as termcolor_colored


class InternalError(Exception):
    pass


class _Test:
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
        # 		mapping['\r'] = '\n'

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

    def run_test(self, compile_command=""):
        if self.debug > 1:
            print(
                f'run_test(compile_command="{compile_command}", command="{self.command}")\n'
            )

        self.set_environ()

        for attempt in range(3):
            if self.debug > 1:
                print("run_test attempt", attempt)
            (stdout, stderr, self.returncode) = run(**self.parameters)
            if stdout or stderr or self.returncode == 0 or not self.expected_stdout:
                break
            if self.debug > 1:
                print("run_test retry", (stdout, stderr, self.returncode))
            # ugly work-around for
            # weird termination with non-zero exit status seen on some CSE servers
            # ignore this execution and try again
            time.sleep(1)

        if self.parameters["unicode_stdout"]:
            self.stdout = codecs.decode(stdout, "UTF-8", errors="replace")
        else:
            self.stdout = stdout

        if self.parameters["unicode_stderr"]:
            self.stderr = codecs.decode(stderr, "UTF-8", errors="replace")
        else:
            self.stderr = stderr

        self.short_explanation = None
        self.long_explanation = None

        stdout_short_explanation = self.check_stream(
            self.stdout, self.expected_stdout, "output"
        )
        if not self.parameters["allow_unexpected_stderr"] or stdout_short_explanation:
            if (
                self.parameters["dcc_output_checking"]
                and "Execution stopped because" in self.stderr
            ):
                self.short_explanation = "incorrect output"
            else:
                self.short_explanation = self.check_stream(
                    self.stderr, self.expected_stderr, "stderr"
                )

        self.stderr_ok = not self.short_explanation

        self.stdout_ok = not stdout_short_explanation

        if not self.short_explanation:
            self.short_explanation = stdout_short_explanation

        if not self.short_explanation:
            self.short_explanation = self.check_files()

        self.test_passed = not self.short_explanation
        if not self.test_passed:
            self.failed_compiler = (
                " ".join(compile_command)
                if isinstance(compile_command, list)
                else str(compile_command)
            )
        return self.test_passed

    def set_environ(self):
        test_environ = self.parameters["environment"]
        if os.environ != test_environ:
            os.environ.clear()
            os.environ.update(test_environ)


def echo_command_for_string(test_input):
    options = []
    if test_input and test_input[-1] == "\n":
        test_input = test_input[:-1]
    else:
        options += ["-n"]
    echo_string = shlex.quote(test_input)
    if "\n" in test_input[:-1]:
        echo_string = echo_string.replace("\\", r"\\")
        options += ["-e"]
    echo_string = echo_string.replace("\n", r"\n")
    command = "echo "
    if options:
        command += " ".join(options) + " "
    return command + echo_string
