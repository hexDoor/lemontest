import os
import sys
import subprocess

from typing import List, Dict, Any

def run_support_command(
    command: List[str],
    stdout=sys.stdout,
    stderr=sys.stderr,
    pass_fds=[],
    arguments: List[str] = None,
    unlink: str = None,
    debug: bool = False,
    environ: Dict[str, Any] = os.environ
) -> int:
    """
    run support command, shell used iff command is a string
    command is not resource-limited, unlike tests
    if unlink is set, it is removed iff it is a symlink, before the command is run
    returns exit code returned by support command
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
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False,
            env=environ # only run with custom environ if set
        )
        # write outputs into stdout and stderr
        stdout.write(p.stdout)
        stderr.write(p.stderr)
        return p.returncode
    except Exception as err:
        stdout.write(str(err))
        return 1