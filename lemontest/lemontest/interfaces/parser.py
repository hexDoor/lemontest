class ParserInterface:
    """
    Interface for parsing
    """

    def parse_arguments(self):
        """
        Parse arguments
        Should return an argparse namespace
        """
        pass

    def parse_tests(self):
        """
        Parse tests
        Should return a list of Test class objects
        """
        pass

    def post_parse_misc(self):
        """
        Execute any post parsing functionality
        (e.g. argument normalisation)
        """
        pass