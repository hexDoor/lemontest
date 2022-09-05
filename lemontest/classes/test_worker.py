class AbstractWorker:
    """
    Abstract test worker class
    """


    def __init__(self):
        """
        Initialise a test worker

        Returns: None
        """
        pass

    def __str__(self):
        """
        Returns a string representation on test worker status

        Returns: str
        """


    def setup(self, **paramaters):
        """
        Perform any necessary setup of the testcase worker
        Should return whether setup was successful

        Returns: bool
        """
        pass


    def support_execute(self, cmd):
        """
        Execute a support shell command
        Should return exit code of the support shell command

        Returns: int
        """


    def execute(self, test):
        """
        Execute a test
        Should return whether the test was executed successfully

        Returns: bool
        """
        pass


    def cleanup(self):
        """
        Perform any necessary cleanup of the testcase worker
        Should return whether cleanup was successful

        Returns: bool
        """
        pass