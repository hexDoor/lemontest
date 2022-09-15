class AbstractParser:
    """
    Abstract parser class
    """

    # standard functions
    def parse_arguments(self):
        """
        Parse arguments
        Sets up an argparse namespace

        Returns: None
        """
        pass


    def parse_tests(self):
        """
        Parse tests

        Returns: None
        """
        pass


    def post_parse_misc(self):
        """
        Execute any post parsing functionality
        (e.g. argument normalisation)

        Returns: None
        """
        pass

    # getters
    def args(self):
        """
        Gets parsed arguments

        Returns: argparse namespace
        """
        pass


    def tests(self):
        """
        Gets parsed arguments

        Returns: Dict(testName, Test)
        """
        pass


    def params(self):
        """
        Gets parsed parameters

        Returns: Dict(paramName, value)
        """
        pass