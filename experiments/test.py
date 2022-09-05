#import unshare
import subprocess
from libc import unshare, CLONE_NEWUSER

#unshare.unshare(unshare.CLONE_NEWUSER)
unshare(0x21)
subprocess.run("whoami")
