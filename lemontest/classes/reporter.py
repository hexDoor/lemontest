class AbstractReporter:
    """
    Abstract reporter class
    """

    # standard functions
    def generate_report(self):
        """
        Generate report of processed tests
        Prints report to stdout
        Optionally uploads test report to a specified url if necessary

        Returns: None
        """
        pass

    def get_exit_code(self):
        """
        Returns exit code status from Reporter

        Returns: int
        """
