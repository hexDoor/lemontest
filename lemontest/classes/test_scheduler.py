class AbstractScheduler:
    """
    Abstract test scheduler class
    """


    def __init__(self):
        """
        Initialise a test scheduler

        Returns: None
        """
        pass

    def __str__(self):
        """
        Returns a string representation on test scheduler status

        Returns: str
        """


    def schedule(self):
        """
        Schedule a test to be executed
        Should return whether the test was scheduled successfully

        Returns: bool
        """
        pass


    def cleanup(self):
        """
        Perform any necessary cleanup of the testcase scheduler
        Should return whether cleanup was successful

        Returns: bool
        """
        pass