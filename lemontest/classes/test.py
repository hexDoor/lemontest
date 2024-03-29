class AbstractTest:
    """
    Abstract test class
    """


    def __init__(self):
        """
        Initialise a test
        You will need to create a test on initialisation
        since it will be easiest to work with test instances

        Returns: None
        """
        pass


    def __str__(self):
        """
        Return a string instatiation of a test

        Returns: str
        """
        pass


    def preprocess(self):
        """
        Execute any preprocessing such as checks etc.
        Should return whether preprocessing succeded
        
        NOTE: This function will most likely contain critical sections
        Ensure critical section safety with synchronisation primitives (mutex lock etc.)

        Returns: bool
        """
        pass


    def run_test(self):
        """
        Execute the test
        Should return whether the test executed successfully

        Returns: bool
        """
        pass


    def postprocess(self):
        """
        Executes any postprocessing such as sanitisation etc.
        Should return whether postprocessing succeded

        Returns: bool
        """
        pass


    def set_environ(self):
        """
        Sets up the environment of the test

        Returns: None
        """
        pass


    def set_param(self):
        """
        Update key value pair in parameter dictionary of the test
        Necessary if we want to change environment with user provided values

        Expects: str, Any
        Returns: None
        """
        pass


    def params(self):
        """
        Returns the parameter dictionary of the test

        Returns: Dict[str, Any]
        """
        pass


    def passed(self):
        """
        Returns whether the test passed or not

        Returns: bool
        """
        pass


    def run_successful(self):
        """
        Returns whether the test was successfully run by a test worker

        Returns: bool
        """
        pass


    def explanation(self):
        """
        Returns an explanation if the test failed, otherwise returns None

        Returns: Union[str, None]
        """

    def mark_timeout(self):
        """
        Mark test failure description as aborted due to timeout

        Returns: None
        """