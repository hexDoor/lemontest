#!/usr/bin/python3

import os
import sys
import re
import signal
import json
import traceback
from collections import OrderedDict

from util.util import die

import legacy_parser.adapter as legacy_parser

# interrupt handler
# TODO: spin down any subprocesses if interrupted
def interrupt_handler(signum, frame):
    os._exit(2)


def execute_autotest():
    # setup parser
    parser = legacy_parser.Parser()
    # execute parser execution
    parser.parse_arguments()
    parser.parse_tests()
    parser.post_parse_misc()

    # check shit is working
    args = parser.args()
    tests = parser.tests()
    if args.print_test_names:
        test_groups = OrderedDict()
        for test in tests.values():
            files = tuple(sorted(test.files))
            test_groups.setdefault(files, []).append(test.label)
        print(
            json.dumps(
                [
                    {"files": files, "labels": labels}
                    for (files, labels) in test_groups.items()
                ]
            )
        )
        return 0

    exit(1)
    # copy files to temp for autotest execustions
    copy_files_to_temp_directory(args, parameters)

    # generate expected outputs if set
    if args.generate_expected_output != "no":
        return generate_expected_output(tests, args)

    # execute autotests
    if parameters.get("upload_url", ""):
        return run_tests_and_upload_results(tests, parameters, args)
    else:
        return run_tests(tests, parameters, args)

# setup environment and config for lemontest
def main():
    # convars
    debug = os.environ.get("AUTOTEST_DEBUG", 0)
    name = re.sub(r"\.py$", "", os.path.basename(sys.argv[0]))

    # load interrupt handler 
    # how do we approach this with multiprocessing pools? (possibly a seperate interrupt handler to kill resources?)
    if not debug:
        signal.signal(signal.SIGINT, interrupt_handler)

    # execute autotests
    try:
        sys.exit(execute_autotest())
    except Exception:
        etype, evalue, _etraceback = sys.exc_info()
        eformatted = "\n".join(traceback.format_exception_only(etype, evalue))
        
        print(f"{name}: internal error: {eformatted}", file=sys.stderr)
        
        if debug:
            traceback.print_exc(file=sys.stderr)

        #print("\n" + REPO_INFORMATION)
        sys.exit(2)

if __name__ == "__main__":
    main()
