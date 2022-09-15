#
# sandbox
# inspired by https://github.com/shubham1172/pocket
# 

import uuid
from cgroupspy import trees

from .util import libc

class SandboxClass:
    debug = False
    sandbox_id = None
    ctree = None

    def __init__(self, **parameters):
        self.debug = parameters["debug"]
        self.sandbox_id = str(uuid.uuid4())

        if self.debug:
            print(f"creating a new sandbox ({self.sandbox_id})")

        # setup cgroup for sandbox:
        self.ctree = trees.Tree()
        # TODO: set cgroup values (or get provided from parameters)

        # mount the file system
        

    def create(self):
        pass

if __name__ == '__main__':
    t = trees.Tree()
    print(t.root.children)
    cset = t.get_node_by_path('/cpuset/')
    print(cset.controller)
    pset = t.get_node_by_path('/pids/')
    print(pset.controller)