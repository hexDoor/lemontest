# shared utility code
# include error classes

import sys
import traceback


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

            print(f"atexit: internal error: {eformatted}", file=sys.stderr)

            if debug:
                traceback.print_exc(file=sys.stderr)
    return wrapper