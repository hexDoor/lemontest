import codecs
import time
import os
import shlex
from termcolor import colored as termcolor_colored
from collections import defaultdict

from interfaces.test import TestInterface
from legacy_test_definition.subprocess_with_resource_limits import run

class Test(TestInterface):
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

    # TODO: add in legacy preprocessing
    def preprocess(self):
        pass

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

    # add in legacy postprocessing
    def postprocess(self):
        pass

    def set_environ(self):
        test_environ = self.parameters["environment"]
        if os.environ != test_environ:
            os.environ.clear()
            os.environ.update(test_environ)

def sanitize_string(
    unsanitized_string,
    leave_tabs=False,
    leave_colorization=False,
    max_lines_shown=32,
    max_line_length_shown=1024,
    # pylint: disable=dangerous-default-value
    line_color=defaultdict(lambda: ""),
    **parameters,
):
    max_lines_shown = int(max_lines_shown)
    max_line_length_shown = int(max_line_length_shown)
    lines = unsanitized_string.splitlines()
    append_repeat_message = False
    if len(lines) >= max_lines_shown:
        last_line_index = len(lines) - 1
        last_line = lines[last_line_index]
        repeats = 1
        while (
            repeats <= last_line_index and lines[last_line_index - repeats] == last_line
        ):
            repeats += 1
        if repeats > max_lines_shown / 2 and len(lines) - repeats < max_lines_shown - 1:
            append_repeat_message = True
            lines = lines[0 : last_line_index + 2 - repeats]

    sanitized_lines = []
    for (line_number, line) in enumerate(lines):
        if line_number >= max_lines_shown:
            sanitized_lines.append("...\n")
            break
        if len(line) > max_line_length_shown:
            line = line[0:max_line_length_shown] + " ..."
        line = line.encode("unicode_escape").decode("ascii")
        if leave_colorization:
            line = line.replace(r"\x1b", "\x1b")
        if leave_tabs:
            line = line.replace(r"\t", "\t")
            line = line.replace(r"\\", "\\")
        color = line_color[line_number]
        if color:
            line = termcolor_colored(line, color)
        sanitized_lines.append(line)
    if append_repeat_message:
        repeat_message = f"<last line repeated {repeats} times>"
        if parameters["colorize_output"]:
            repeat_message = termcolor_colored(repeat_message, "red")
        sanitized_lines.append(repeat_message)
    return "\n".join(sanitized_lines) + "\n"

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
