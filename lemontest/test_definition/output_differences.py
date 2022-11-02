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
