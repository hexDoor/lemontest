from interfaces.parser import ParserInterface
import command_line_arguments as cmdlineargs
import parse_test_specification as parsetestspec

class Parser(ParserInterface):
    # standard vars
    _args = None
    _tests = None
    _params = None

    # getters
    def args(self):
        return self._args
    
    def tests(self):
        return self._tests
    
    def params(self):
        return self._params

    # argument and test parsing functionality

    # literally a reordering of the original autotest parser but done in a way
    # that made some sense (and was easier to work with)
    # for whoever comes after, i tried untangling all the dependencies
    # what you see here is myself giving up on that because the more I tried,
    # the more I realised how pointless it was since it doesn't give much
    # performance benefit anyway.
    # Oh yeah, the original parser is O(N^2) so as soon as you start
    # having more tests, glhf
    # please use the interface to rewrite a new parser that actually makes sense
    def parse_arguments(self):
        self._args = cmdlineargs.parse_arguments()

    def parse_tests(self):
        test_specification_pathname = cmdlineargs.find_test_specification(self._args)
        tests_as_dicts, self._params = parsetestspec.parse_file(
            test_specification_pathname,
            initial_parameters=self._args.initial_parameters,
            initial_tests=self._args.initial_tests,
            debug=self._args.debug,
        )
        self._tests = dict(
            (label, _Test(self._args.autotest_directory, **t))
            for (label, t) in tests_as_dicts.items()
        )

    def post_parse_misc(self):
        cmdlineargs.normalize_arguments(self._args, self._tests)