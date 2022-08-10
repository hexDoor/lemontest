import os
import re
import sys


def parse_tests():
    pass

def find_test_specification(args):
    if not args.exercise_directory and not args.autotest_directory and args.exercise:
        test_specification_pathname = load_embedded_autotest(args.exercise)
        if test_specification_pathname:
            args.test_specification_pathname = test_specification_pathname
            args.autotest_directory = os.path.dirname(test_specification_pathname)
            return test_specification_pathname

    if not args.exercise_directory:
        args.exercise_directory = ["."]

    # FIXME - generalize this code
    if args.autotest_directory:
        if os.path.isfile(args.autotest_directory):
            args.test_specification_pathname = args.autotest_directory
            args.autotest_directory = os.path.dirname(args.autotest_directory) + "/"
            return args.test_specification_pathname
        exercise = ""
        exercise_directories = [args.autotest_directory]
        if args.marking:
            sub_pathnames = ["automarking,txt", "tests.txt"]
        else:
            sub_pathnames = ["tests.txt"]
    else:
        exercise_directories = args.exercise_directory
        exercise = args.exercise
        if args.marking:
            sub_pathnames = [
                "automarking,txt",
                "automarking/tests.txt",
                "automarking/automarking.txt",
            ]
        else:
            sub_pathnames = [
                "tests.txt",
                "autotest/tests.txt",
                "autotest/automarking.txt",
            ]

    test_specification_pathname = find_autotest_dir(
        exercise_directories, exercise, sub_pathnames, debug=args.debug
    )

    if not args.autotest_directory:
        args.autotest_directory = os.path.dirname(test_specification_pathname)

    args.autotest_directory = os.path.realpath(args.autotest_directory)

    if args.autotest_directory[-1] != "/":
        args.autotest_directory += "/"
    if args.debug:
        print("autotest_dir:", args.autotest_directory, file=sys.stderr)

    args.test_specification_pathname = os.path.realpath(test_specification_pathname)
    return args.test_specification_pathname


def find_autotest_dir(exercise_directories, exercise, sub_pathnames, debug=0):
    """
    search for a test specification file
    """

    # for convenience massage exercise name into several possibilities
    # so for example is exercises is specified as prime.c
    # we try prime as an exercise name if prime.c doesn't exist
    # similarly prime will be tried  if lab03_prime is the exercise name

    exercise_alternative_names = [exercise]
    if "." in exercise:
        exercise_alternative_names.append(re.sub(r"\..*", "", exercise))

    # should this code be generalized?
    m = re.match(r"(\w+?\d{1,2}[ab]?_)(.*)", exercise)
    if m:
        exercise_alternative_names.append(re.sub(r"\..*", "", m.group(2)))

    m = re.match(r"(\w+\d{1,2}[ab]?_)(.*)", exercise)
    if m:
        exercise_alternative_names.append(re.sub(r"\..*", "", m.group(2)))

    for exercise_directory in exercise_directories:
        for possible_exercise_name in exercise_alternative_names:
            for sub_pathname in sub_pathnames:
                path = os.path.join(
                    exercise_directory, possible_exercise_name, sub_pathname
                )
                if debug > 2:
                    print("looking for test specification in", path)
                if os.path.exists(path):
                    if debug > 1:
                        print("test specification found in", path)
                    return path
    if exercise:
        die(f"no autotest found for {exercise}")
    else:
        die("no autotest found")
    sys.exit(0)