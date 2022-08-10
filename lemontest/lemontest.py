#!/usr/bin/python3

import os
import sys
import re
import signal
import traceback

import legacy_parser.adapter as Parser
import test_scheduler.test_scheduler as TestScheduler

# interrupt handler
# TODO: spin down any subprocesses if interrupted
def interrupt_handler(signum, frame):
    os._exit(2)


def execute_autotest():
    # setup parser
    parser = Parser.Parser()
    # execute parser execution
    parser.parse_arguments()
    parser.parse_tests()
    parser.post_parse_misc()

    # setup test scheduler
    test_scheduler = TestScheduler.TestScheduler()
    test_scheduler.setup(parser.args())
    # execute tests
    test_scheduler.schedule(parser.tests())
    # await execution finish and cleanup
    test_scheduler.cleanup()

    # TODO: send tests to output processor
    # TODO: post autotest cleanup/misc actions
    
    return 0


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
