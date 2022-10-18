from .util import die

from pathlib import Path
from shutil import copy2, copystat

import glob
import os
import sys
import re
import subprocess
import shutil

# Returns False if expected files are missing, True otherwise.
def copy_files_to_directory(dir_path: Path, parameters, args):
    dir = dir_path.resolve()
    if parameters["supplied_files_directory"]:
        copy_directory(parameters["supplied_files_directory"], dir)

    # fetch student submission into shared_dir
    fetch_submission(dir, args)

    # added for COMP1521 shell assignment but probably a good idea generally
    # os.environ['HOME'] = temp_dir

    for expected_file in glob.glob(f"{dir}/*.expected_*"):
        os.chmod(expected_file, 0o400)


def fetch_submission(temp_dir, args):
    if args.debug:
        print(f"fetch_submission({temp_dir})", file=sys.stderr)
    if args.tarfile:
        die("tar not supported")
    elif args.directory:
        copy_directory(args.directory, temp_dir)
    elif args.git:
        die("git not supported")
    else:
        files_to_copy = set(args.file | args.optional_files)
        # stin file?
        if args.stdin:
            if len(files_to_copy) != 1:
                print(
                    "--stdin specified but tests requires multiple files",
                    file=sys.stderr,
                )
                sys.exit(1)
            file = files_to_copy.pop()
            try:
                file_path = os.path.join(temp_dir, file)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(sys.stdin.read())
            except IOError:
                die(f"can not create {file}")
            return
        
        # actual copying of files
        if args.debug:
            print("files_to_copy:", files_to_copy, file=sys.stderr)
        copied = set()
        while files_to_copy:
            file_pattern = files_to_copy.pop()
            if file_pattern in copied:
                continue
            copied.add(file_pattern)
            for file in glob.glob(file_pattern):
                try:
                    # don't overwrite files which are supplied by the autotest
                    # can break old autotests
                    if os.path.exists(os.path.join(temp_dir, file)):
                        continue
                    shutil.copy(file, temp_dir)
                    if re.search(r"\.[pc].?$", file):
                        try:
                            # Kludge to pick up include files
                            with open(file, encoding="utf-8") as f:
                                for line in f:
                                    m = re.search(
                                        r'\b(require|include)\s*[\'"](.*?)[\'"]',
                                        line,
                                        flags=re.I,
                                    )
                                    if m:
                                        files_to_copy.add(m.group(2))
                                    m = re.search(
                                        r"^\s*\b(use|require)\s*(\S+)", line, flags=re.I
                                    )
                                    if m:
                                        files_to_copy.add(m.group(2) + ".pm")
                        except UnicodeDecodeError:
                            die(f"{file} is not a text file")
                except IOError:
                    continue


def execute(command, print_command=True):
    if print_command:
        print(" ".join(command))
    if subprocess.call(command) != 0:
        die(f"{command[0]} failed")


def copy_directory(src, dst, symlinks=False, ignore=None):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not (os.path.exists(dst) and os.path.isdir(dst)):
        os.makedirs(dst)
        # we don't want to copy directory permission if the directory exists already
        try:
            copystat(src, dst)
        except OSError:
            pass
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copy_directory(srcname, dstname, symlinks, ignore)
            else:
                copy2(srcname, dstname)
        except OSError as why:
            # we don't want to stop if there is an unreadable file - just produce an error
            print("Warning:", why, file=sys.stderr)