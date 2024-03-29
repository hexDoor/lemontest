#!/usr/bin/python3

import legacy_parser.adapter as Parser
import test_scheduler.test_scheduler as TestScheduler
import reporter.reporter as Reporter

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

    # Report Module
    reporter = Reporter.Reporter(parser.args(), parser.params())
    # generate report
    reporter.generate_report(processed_tests)
    # get exit code
    reporter_exit = reporter.get_exit_code()

    # TODO: post autotest cleanup/misc actions

    return reporter_exit


# setup environment and config for lemontest
def main():
    # convars
    debug = os.environ.get("AUTOTEST_DEBUG", 0)
    name = re.sub(r"\.py$", "", os.path.basename(sys.argv[0]))

    # execute autotests
    try:
        sys.exit(execute_autotest())
    except Exception:
        etype, evalue, _etraceback = sys.exc_info()
        eformatted = "\n".join(traceback.format_exception_only(etype, evalue))

        print(f"Error encountered while running autotests:", f"{evalue}", sep='\n\n', file=sys.stderr)

        if debug:
            traceback.print_exc(file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    if sys.platform != 'linux':
        print("lemontest is not supported on non-linux systems")
        sys.exit(1)
    main()
