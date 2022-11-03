from util.util import InternalError

import re
import subprocess


def make_string_canonical(raw_str, canonical_translator, parameters, keep_all_lines=False):
    debug = parameters["debug"]
    s = re.sub("\r\n?", "\n", raw_str)
    filter = parameters.get("postprocess_output_command", None)

    if filter:
        if debug:
            print(f"postprocess_output_command={filter} str='{s}'")
        # FIXME: Design break with run_suppport_command which this is a support command
        # I don't see a reasonable way to put this in the test without lots of reorg
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

    if parameters["ignore_case"]:
        s = s.lower()
    s = s.translate(canonical_translator)
    if parameters["ignore_blank_lines"] and not keep_all_lines:
        s = re.sub(r"\n\s*\n", "\n", s)
        s = re.sub(r"^\n+", "", s)
    if parameters["ignore_trailing_whitespace"]:
        s = re.sub(r"[ \t]+\n", "\n", s)
    if debug:
        print(f"make_string_canonical('{raw_str}') -> '{s}'")
    return s


def compare_strings(actual, expected, canonical_translator, parameters):
    return make_string_canonical(actual, canonical_translator, parameters) == make_string_canonical(expected, canonical_translator, parameters)
