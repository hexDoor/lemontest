import os
import sys
import re
import signal
import traceback

def interrupt_handler(signum, frame):
    pass
    

# setup environment and config for lemontest
def main():
    # convars
    debug = os.environ.get("AUTOTEST_DEBUG", 0)
    name = re.sub(r"\.py$", "", os.path.basename(sys.argv[0]))

    # load interrupt handler 
    # how do we approach this with multiprocessing pools? (possibly a seperate interrupt handler to kill resources?)
    if not debug:
        signal.signal(signal.SIGINT, interrupt_handler)

    try:
        sys.exit(execute_autotest):
    except Exception as err:
        etype, evalue, _etraceback = sys.exc_info()
        eformatted = "\n".join(traceback.format_exception_only(etype, evalue))
        
        print(f"{name}: internal error: {eformatted}", file=sys.stderr)
        
        if debug:
            traceback.print_exc(file=sys.stderr)

        #print("\n" + REPO_INFORMATION)
        sys.exit(2)

if __name__ == "__main__":
    main()
