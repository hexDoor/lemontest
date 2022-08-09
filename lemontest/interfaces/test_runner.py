class RunnerInterface:
    """
    Interface for test runner
    """


    def __init__(self):
        """
        Initialise a test runner

        Returns: None
        """
        pass

    def __str__(self):
        """
        Returns a string representation on test runner status

        Returns: str
        """


    def setup(self):
        """
        Perform any necessary setup of the testcase runner
        Should return whether setup was successful

        Returns: bool
        """
        pass


    def schedule(self):
        """
        Schedule a test to be executed
        Should return whether the test was scheduled successfully

        Returns: bool
        """
        pass


    def cleanup(self):
        """
        Perform any necessary cleanup of the testcase runner
        Should return whether cleanup was successful

        Returns: bool
        """
        pass