# shared utility code
# include error classes


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