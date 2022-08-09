class ParserInterface:
    """
    Interface for parsing
    """


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