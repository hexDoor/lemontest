#!/usr/bin/python3

import os
import sys
import re
import signal
import json
from collections import OrderedDict

from util.util import die

from parser.argument_parser import argument_parser
from parser.test_parser import test_parser

from legacy_parser.command_line_arguments import process_arguments

# interrupt handler
# TODO: spin down any subprocesses if interrupted
def interrupt_handler(signum, frame):
    os._exit(2)


def execute_autotest():
    # FIXME: use legacy parser
    args, tests, parameters = process_arguments()

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
