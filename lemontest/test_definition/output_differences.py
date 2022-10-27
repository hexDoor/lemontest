from util.util import InternalError

import re
import subprocess


def make_string_canonical(raw_str, keep_all_lines=False, debug=False):
    s = re.sub("\r\n?", "\n", raw_str)
    filter = self.parameters.get("postprocess_output_command", None)

    if filter:
        if debug:
            print(f"postprocess_output_command={filter} str='{s}'")
        p = subprocess.run(
            filter,
            stdout=subprocess.PIPE,
            input=s,
            stderr=subprocess.PIPE,
            shell=isinstance(filter, str),
            universal_newlines=True,
        )
        if p.stderr:
            raise InternalError(
                "error from postprocess_output_command: " + p.stderr
            )
        if p.returncode:
            raise InternalError(
                "non-zero exit status from postprocess_output_command"
            )
        s = p.stdout
        if debug:
            print(f"after filter s='{s}'")

    if self.parameters["ignore_case"]:
        s = s.lower()
    s = s.translate(self.canonical_translator)
    if self.parameters["ignore_blank_lines"] and not keep_all_lines:
        s = re.sub(r"\n\s*\n", "\n", s)
        s = re.sub(r"^\n+", "", s)
    if self.parameters["ignore_trailing_whitespace"]:
        s = re.sub(r"[ \t]+\n", "\n", s)
    if self.debug > 1:
        print(f"make_string_canonical('{raw_str}') -> '{s}'")
    return s

def compare_strings(actual, expected):
    return make_string_canonical(actual) == make_string_canonical(expected)

def check_stream(actual, expected, name, debug=False):
    if debug:
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
            if compare_strings(actual, expected):
                return None
            else:
                return "Incorrect " + name
        else:
            if name == "stderr":
                return "errors"
            elif name == "stdout":
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

def check_files():
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
            self.file_not_ok = pathname
            self.file_expected = expected_contents
            self.file_actual = actual_contents
            return short_explanation
