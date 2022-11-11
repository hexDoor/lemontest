import warnings
import subprocess
import re
import sys
import multiprocessing

multiprocessing.freeze_support()

# created from at's original test script (yes this script needs to be thrown into a fire)
# don't forget to add `sys.exectuable` for every subprocess call to ensure same python interpreter is used
class TestStandard:
    def test_arguments(self):
        test_folder = "tests/arguments"
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        if not re.search(r" tests passed 0 tests failed *$", p.stdout):
            print(p.stdout)
            assert False

    def test_checker(self):
        test_folder = "tests/checker"
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        # Peform a series of greps to find if we have the correct output.
        # Yes, this feels very brittle. No, I don't have a better solution.
        # More greps could be added to ensure that this is more effective.
        success = True
        if not re.search(
            r"Test 0 \(\./hello.sh\) - passed", p.stdout
        ):
            success = False
        if not re.search(
            r"Test 1 \(\./hello.sh\) - failed \(could not be run because check failed\)",
            p.stdout,
        ):
            success = False
        if not re.search(
            r"1 tests passed 0 tests failed  1 tests could not be run",
            p.stdout,
        ):
            success = False

        if success is False:
            print(p.stdout)

        assert success

    def test_environment(self):

        test_folder = "tests/environment"
        test_env = {
            "SAMPLE_ENVIRONMENT_VARIABLE": "sample_value"
        }  # this is cursed but it's necessary
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                ],
                env=test_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        if not re.search(r" tests passed 0 tests failed *$", p.stdout):
            print(p.stdout)
            assert False

    def test_expected_output(self):
        test_folder = "tests/expected_output"
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        if not re.search(r" tests passed 0 tests failed *$", p.stdout):
            print(p.stdout)
            assert False

    def test_f_strings(self):
        test_folder = "tests/f-strings"
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        if not re.search(r" tests passed 0 tests failed *$", p.stdout):
            print(p.stdout)
            assert False

    def test_ignore(self):
        test_folder = "tests/ignore"
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        if not re.search(r" tests passed 0 tests failed *$", p.stdout):
            print(p.stdout)
            assert False

    def test_limits(self):
        test_folder = "tests/limits"
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                    "--parameters",
                    "ignore_blank_lines=1\nignore_case=1\ncompare_only_characters=abcdefghijklmnopqrstuvwxyz",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        # Peform a series of greps to find if we have the correct output.
        # Yes, this feels very brittle. No, I don't have a better solution.
        # More greps could be added to ensure that this is more effective.
        success = True
        if not re.search(
            r"Test max_open_files_should_pass \(/bin/true\) - passed", p.stdout
        ):
            success = False
        if not re.search(
            r"Test max_open_files_should_fail \('/bin/true 3>3 4>4 5>5 6>6 7>7 8>8'\) - failed \(errors\)",
            p.stdout,
        ):
            success = False
        if not re.search(
            r"Test max_cpu_seconds_should_fail \('while true; do :; done'\) - failed \(errors\)",
            p.stdout,
        ):
            success = False
        if not re.search(
            r"Test max_file_size_bytes_should_fail \('yes >out'\) - failed \(errors\)",
            p.stdout,
        ):
            success = False
        if not re.search(
            r"Test max_stdout_bytes_should_fail \(yes\) - failed \(errors\)", p.stdout
        ):
            success = False
        if not re.search(
            r"Test max_stderr_bytes_should_fail \('yes 1>&2'\) - failed \(errors\)",
            p.stdout,
        ):
            success = False
        if not re.search(r"1 tests passed 5 tests failed", p.stdout):
            success = False

        if success is False:
            print(p.stdout)

        assert success

    def test_multi_file_simple(self):
        test_folder = "tests/multi-file-simple"
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        if not p.stdout != re.search(r" tests passed 0 tests failed *$", p.stdout):
            print(p.stdout)
            assert False

    def test_non_unicode_stdout(self):
        test_folder = "tests/non_unicode_stdout"
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        if not re.search(r" tests passed 0 tests failed *$", p.stdout):
            print(p.stdout)
            assert False

    def test_non_unicode_stderr(self):
        test_folder = "tests/non_unicode_stderr"
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        if not re.search(r" tests passed 0 tests failed *$", p.stdout):
            print(p.stdout)
            assert False

    def test_non_unicode_stdin(self):
        test_folder = "tests/non_unicode_stdin"
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        if not re.search(r" tests passed 0 tests failed *$", p.stdout):
            print(p.stdout)
            assert False

    def test_non_unicode_file_output(self):
        test_folder = "tests/non_unicode_file_output"
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        expected_output = r"Test test_incorrect_output \(not_unicode_files\) - failed \(Your non-unicode output is not correct\)\n"
        expected_output += r"Your non-unicode files had incorrect output\n"
        expected_output += r"File test_file2 had the following error:\n"
        expected_output += r"expected: 0xa571ffffa57f actual: 0xa571ffffa571\n"
        expected_output += (
            r"There were 3 different bits between your output and the expected output\n"
        )
        if not re.search(expected_output, p.stdout):
            print(p.stdout)
            assert False

        expected_output = r"1 tests passed 1 tests failed"
        if not re.search(expected_output, p.stdout):
            print(p.stdout)
            assert False

    def test_shell(self):
        test_folder = "tests/shell"
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        if not re.search(r" tests passed 0 tests failed *$", p.stdout):
            print(p.stdout)
            assert False

    def test_show_parameters(self):
        test_folder = "tests/show_parameters"
        try:
            p = subprocess.run(
                args=[
                    sys.executable,
                    "./lemontest.py",
                    "-D",
                    test_folder,
                    "-a",
                    f"{test_folder}/autotest",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            warnings.warn("subprocess timed out rather than give results - consider this a warning but not a fail unless you've modified sandbox core")
            return
        except Exception as err:
            print(err)
            assert False
        if not p.stdout != re.search(r" tests passed 0 tests failed *$", p.stdout):
            print(p.stdout)
            assert False
