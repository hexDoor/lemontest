import argparse
import os
import re
import sys
from util.util import die
from parser.parser_util import parse_string

def parse_arguments():
    # initialise parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # add standard arguments
    parser.add_argument(
        "-a", "--autotest_directory", help="DIRECTORY containing test specification"
    )
    parser.add_argument(
        "-c", "--commit", help="test files from COMMIT instead of latest commit"
    )
    parser.add_argument("-d", "--debug", action="count", help="print debug information")
    parser.add_argument("-e", "--exercise", help="run tests for EXERCISE")
    parser.add_argument(
        "-E",
        "--exercise_directory",
        action="append",
        help="parent DIRECTORY containing exercises",
    )
    parser.add_argument(
        "-f",
        "--file",
        nargs="+",
        default=[],
        help="add a copy of this file to the test directory ",
    )
    parser.add_argument(
        "-g",
        "--generate_expected_output",
        nargs="?",
        const="stdout",
        default="no",
        help="generate expected output for tests based on supplied solution",
    )
    parser.add_argument(
        "-l", "--labels", nargs="+", default=[], help="execute tests with these LABELS"
    )
    parser.add_argument(
        "-m", "--marking", action="store_true", help="run automarking tests"
    )

    parser.add_argument(
        "--print_test_names", action="store_true", help="print names of tests and files"
    )
    parser.add_argument(
        "-p", "--programs", nargs="+", default=[], help="execute tests for PROGRAMS"
    )
    parser.add_argument(
        "-P", "--parameters", help="set parameter values", action="append"
    )
    parser.add_argument("extra_arguments", nargs="*", default=[], help="")

    # handle specialised and deprecated arguments
    source_args = parser.add_mutually_exclusive_group()
    add_mutually_exclusive_arguments(source_args)
    add_obsolete_arguments(parser)

    # parse arguments
    args = parser.parse_args()

    # post-parse checks
    check_obsolete_arguments(args)

    # set default arguments
    args.debug = int(args.debug or os.environ.get("AUTOTEST_DEBUG", 0) or 0)


    # FIXME: Legacy Check
    #argument_parser_legacy(args)

    return args


def add_mutually_exclusive_arguments(parser):
    parser.add_argument(
        "-D", "--directory", help="add files from this directory to the test directory"
    )
    parser.add_argument(
        "-G",
        "--git",
        help="add files from this this git repository to the test directory",
    )
    parser.add_argument(
        "-S",
        "--stdin",
        action="store_true",
        help="test file supplied on standard input",
    )
    parser.add_argument(
        "-t",
        "--tarfile",
        help="add files from this tarfile to the test directory, can be http URL",
    )

    # these CSE specific parameters should be move parameters which can be specified in a shell wrapper
    parser.add_argument(
        "--gitlab_cse",
        action="store_true",
        help="deprecated: test files from gitlab.cse.unsw.edu.au",
    )
    parser.add_argument(
        "--student",
        help="deprecated: test files from STUDENT's repository on gitlab.cse.unsw.edu.au",
    )


def add_obsolete_arguments(parser):
    """
    add obsolete arguments so we can give a helpful message before dying if they are used
    """
    parser.add_argument("-C", "--c_compilers", help=argparse.SUPPRESS)
    parser.add_argument("--c_checkers", help=argparse.SUPPRESS)
    # 	parser.add_argument("-j", "--json", help=argparse.SUPPRESS)
    parser.add_argument("--colorize", dest="colorize", help=argparse.SUPPRESS)
    parser.add_argument("--no_colorize", dest="colorize", help=argparse.SUPPRESS)
    parser.add_argument("--no_show_input", dest="show_input", help=argparse.SUPPRESS)
    parser.add_argument(
        "--no_show_expected", dest="show_expected", help=argparse.SUPPRESS
    )
    parser.add_argument("--no_show_actual", dest="show_actual", help=argparse.SUPPRESS)
    parser.add_argument("--no_show_diff", dest="show_diff", help=argparse.SUPPRESS)
    parser.add_argument(
        "--no_show_reproduce_command",
        dest="show_reproduce_command",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--no_check_hash_bang_line", dest="check_hash_bang_line", help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--no_fail_tests_for_errors",
        dest="fail_tests_for_errors",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--show_stdout_if_errors", dest="show_stdout_if_errors", help=argparse.SUPPRESS
    )
    parser.add_argument("--ssh_upload_url", help=argparse.SUPPRESS)
    parser.add_argument("--ssh_upload_host", help=argparse.SUPPRESS)
    # 	parser.add_argument("--ssh_upload_username", help=argparse.SUPPRESS)
    # 	parser.add_argument("--ssh_upload_keyfile", help=argparse.SUPPRESS)
    # 	parser.add_argument("--ssh_upload_key", help=argparse.SUPPRESS)
    parser.add_argument("--ssh_upload_max_bytes", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--no_style", help=argparse.SUPPRESS)


# link obsolete argument to a parameter making it obsolete
PARAMETERS_MATCHING_OBSOLETE_ARGUMENTS = [
    ("c_compilers", "default_compilers"),
    ("c_checkers", "default_checkers"),
    ("colorize", "colorize_output"),
    ("show_input", "show_stdin"),
    ("show_expected", "show_reproduce_command"),
    ("show_stdout_if_errors", "show_stdout_if_errors"),
    ("no_fail_tests_for_errors", "allow_unexpected_stderr"),
    ("ssh_upload_url", "upload_url"),
    ("ssh_upload_max_bytes", "upload_max_bytes"),
    ("no_style", "default_checkers"),
]


def check_obsolete_arguments(args):
    """
    give helpful message for obsolete arguments then die
    """
    for (argument, parameter_name) in PARAMETERS_MATCHING_OBSOLETE_ARGUMENTS:
        if getattr(args, argument, None) is not None:
            print(getattr(args, argument))
            die(
                f"argument '{argument}' no longer supported, instead use -P to specify an equivalent value for parameter '{parameter_name}'"
            )


def argument_parser_legacy(args):
    # old debug arg set

    # TODO: WTF does this do?
    args.initial_tests, args.initial_parameters = parse_string(
        "\n".join(args.parameters or ""),
        source_name="<command-line argument>",
        normalize_global_parameters=False,
        debug=args.debug,
    )

    # backwards compatibility
    args.initial_parameters.setdefault("debug", args.debug)

    # raw argument debug print
    if args.debug:
        print("raw args:", args, file=sys.stderr)

    # TODO: WTF does this do?
    if len(args.extra_arguments) == 2 and re.search(r"\.tar$", args.extra_arguments[0]):
        # give calls dryrun this way
        args.tarfile = args.extra_arguments[0]
        args.exercise = args.extra_arguments[1]
        args.extra_arguments = []

    # checks existence of either exercises or the autotest directory
    # WTF IS THIS EXTRA_ARGUMENTS BS?????????
    if not args.exercise and not args.autotest_directory:
        if args.extra_arguments:
            args.exercise = args.extra_arguments.pop(0)
        else:
            die("no exercise specified")

    # THIS THING SETS EXERCISE TO THE DIRECTORY PATH?????????????????????????????????
    if not args.exercise and args.autotest_directory:
        args.exercise = os.path.basename(args.autotest_directory)
