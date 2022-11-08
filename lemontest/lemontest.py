#!/usr/bin/python3

import legacy_parser.adapter as Parser
import test_scheduler.test_scheduler as TestScheduler

from termcolor import colored as termcolor_colored

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
        else lambda x, *a, **kw: x
    )
    failed_tests = [test for test in processed_tests if not test.passed()]
    for test in processed_tests:
        print(test)
    pass_str = colored(f"{len(processed_tests) - len(failed_tests)} tests passed", "green")
    fail_str = colored(f"{len(failed_tests)} tests failed", "red")
    print(f"{pass_str} {fail_str}")

    # TODO: post autotest cleanup/misc actions
    # TODO: upload to cgi?
    # TODO: send tests to output module (prettier output)

    return 0


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
