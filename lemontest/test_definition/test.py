from classes.test import AbstractTest

class Test(AbstractTest):

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