#!/usr/bin/python3

import legacy_parser.adapter as Parser
import test_scheduler.test_scheduler as TestScheduler

from termcolor import colored as termcolor_colored
from util.util import lambda_function

import os
import sys
import re
import traceback

def execute_autotest():
    # setup parser
    parser = Parser.Parser()
    # execute parser execution
    parser.parse_arguments()
    parser.parse_tests()
    parser.post_parse_misc()

    # setup test scheduler
    test_scheduler = TestScheduler.TestScheduler(parser.args(), parser.params())
    # schedule execute tests
    processed_tests = test_scheduler.schedule(parser.tests())
    # await execution finish and cleanup
    test_scheduler.cleanup()

    # get failed_tests or exit early if everything passed
    colored = (
        termcolor_colored
        if parser.params()["colorize_output"]
        else lambda_function
    )
    failed_count = 0
    not_run_count = 0
    seen_errors = {}
    # i really don't like this personally but getting "same as test blah" requires this
    # same for not_run_tests
    for test in processed_tests:
        if not test.passed():
            print(test.explanation(seen_errors))
            if not test.run_successful():
                not_run_count += 1
            else:
                failed_count += 1
        else:
            print(test)
    pass_str = colored(f"{len(processed_tests) - failed_count - not_run_count} tests passed", "green")
    fail_str = colored(f"{failed_count} tests failed", "red")
    if not_run_count:
        # two spaces before tests could not be run for some reason
        print(f"{pass_str} {fail_str}  {not_run_count} tests could not be run")
    else:
        print(f"{pass_str} {fail_str}")

    # TODO: post autotest cleanup/misc actions
    # TODO: upload to cgi?
    # TODO: send tests to output module (prettier output)

    return 1 if failed_count + not_run_count else 0


# setup environment and config for lemontest
def main():
    # convars
    debug = os.environ.get("AUTOTEST_DEBUG", 0)
    name = re.sub(r"\.py$", "", os.path.basename(sys.argv[0]))

    # load interrupt handler 
    # how do we approach this with multiprocessing pools? (possibly a seperate interrupt handler to kill resources?)
    # probably not necessary (just let it die by itself hahaaa)

    # execute autotests
    try:
        sys.exit(execute_autotest())
    except Exception:
        etype, evalue, _etraceback = sys.exc_info()
        eformatted = "\n".join(traceback.format_exception_only(etype, evalue))

        print(f"{name}: internal error: {eformatted}", file=sys.stderr)

        if debug:
            traceback.print_exc(file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    if sys.platform != 'linux':
        print("lemontest is not supported on non-linux systems")
        sys.exit(1)
    main()
