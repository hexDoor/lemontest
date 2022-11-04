#!/usr/bin/python3
import subprocess

test_spec = """
max_cpu=30
command=1521 mipsy snake.s
files=snake.s

.
a
d
s
w
wa
wwwwwwwaaaaa
wwwwwwwaaaaaa
wawawawawawaw
wwwwwwwaaaaaasdw
wwwwwwwaaaaaasssssddd
ssssssss
dddddddd
wwwwwwww
"""

subprocess.run(['clang','../files.ln/snake.c'])
test_number = 0
for line in test_spec.splitlines():
    line = line.strip()
    if not line or '=' in line:
        print(line)
        continue
    test_number += 1
    p = subprocess.run(f'./a.out {line}', input=line, shell=True, capture_output=True, universal_newlines=True)
    expected_stdout = ''
    # autotest mis-interprets tabs - so avoid them
    expected_stdout += p.stdout.replace('\n', '\\n').replace('\t', ' ')
    stdin = line.replace(' ', '\\n') + '\\n'
    print(f'{test_number} stdin="{stdin}" description="{line}" expected_stdout="{expected_stdout}"')
