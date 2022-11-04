#!/usr/bin/python3
print("""
max_cpu=30
command=1521 mipsy ackermann.s
files=ackermann.s

""")

tests = [
    (0, 0),
    (0, 1),
    (0, 2),
    (1, 0),
    (1, 1),
    (1, 2),
    (2, 0),
    (2, 1),
    (2, 2),
    (3, 0),
    (3, 1),
    (3, 2),
    (4, 0)
]

for (test_number, (m, n)) in enumerate(tests):
    print(f'{test_number} description="Ackermann({m}, {n})" stdin="{m}\\n{n}\\n"')
