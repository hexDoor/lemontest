import os
import sys
import subprocess

from typing import List

def run_support_command(
    command: List[str],
    file=sys.stdout,
    arguments: List[str] = None,
    unlink: str = None,
    debug: bool = False,
) -> bool:
    """
    run support command, shell used iff command is a string
    command is not resource-limited, unlike tests
    if unlink is set, it is removed iff it is a symlink, before the command is run
    return True if command has 0 exit status, False otherwise
    """
    arguments = arguments or []
    if isinstance(command, str):
        cmd = command + " " + " ".join(arguments)
    else:
        cmd = command + arguments

    if unlink and os.path.exists(unlink) and os.path.islink(unlink):
        os.unlink(unlink)

    try:
        p = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            input="",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT if debug else subprocess.DEVNULL,
            universal_newlines=True,
            check=False,
        )
        file.write(p.stdout)
        result = p.returncode == 0
        return result
    except Exception as err:
        file.write(str(err))
        return False