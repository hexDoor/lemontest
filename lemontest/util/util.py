# shared utility code
# include error classes

import sys
import traceback

SIGINT_MESSAGE = "User sent SIGINT. Please try to let your autotest process complete rather than trying to force quit it."


class AutotestException(Exception):
    pass


class TestSpecificationError(AutotestException):
    pass


class InternalError(AutotestException):
    pass


def die(message):
    raise InternalError(message)


# INFO: This is necessary because pytest won't play nice with lambda functions
# Just replace any lambda that will return just the first argument with this
def lambda_function(x, *a, **kw):
    return x


# atexit function exception formatting wrapper
# Necessary otherwise any atexit function that raises an exception has not so nice
# formatting
def atexit_exc_decorator(func, debug):
    def wrapper(*a, **kw):
        try:
            func(*a, **kw)
        except Exception:
            etype, evalue, _etraceback = sys.exc_info()
            eformatted = "\n".join(traceback.format_exception_only(etype, evalue))

            print(f"Error encountered when exiting:", f"{evalue}", sep='\n\n', file=sys.stderr)

            if debug:
                traceback.print_exc(file=sys.stderr)
    return wrapper


# plagiarised Tee code from old autotest (deal with it)
class Tee:
    def __init__(self, stream):
        self.stream = stream
        self.fileno = stream.fileno

    def flush(self):
        sys.stdout.flush()
        self.stream.flush()

    def write(self, message):
        sys.stdout.write(message)
        self.stream.write(message)

    def getStream(self):
        return self.stream

    def close(self):
        self.stream.close()