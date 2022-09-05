from classes.test_worker import AbstractScheduler


class TestScheduler(AbstractScheduler):
    def __init__(self):
        pass

    def __str__(self):
        pass

    def setup(self, parameters):
        pass

    def schedule(self, tests):
        for test in tests.values():
            print(test)

    def cleanup(self):
        pass