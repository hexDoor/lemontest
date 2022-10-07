#!/usr/bin/python3

import os
import sys
import re
import signal
import traceback

import legacy_parser.adapter as Parser
import test_scheduler.test_scheduler as TestScheduler

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

    # TODO: send tests to output processor
    # TODO: post autotest cleanup/misc actions
    print(processed_tests)
    print()

    return 0


# setup environment and config for lemontest
def main():
    # convars
    debug = os.environ.get("AUTOTEST_DEBUG", 0)
    name = re.sub(r"\.py$", "", os.path.basename(sys.argv[0]))

    # load interrupt handler 
    # how do we approach this with multiprocessing pools? (possibly a seperate interrupt handler to kill resources?)
    #if not debug:
        #signal.signal(signal.SIGINT, interrupt_handler)

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


# kill everything
def kill_all():
    pass

if __name__ == "__main__":
    main()
