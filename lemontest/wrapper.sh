#!/bin/sh

parameters="
	dcc_output_checking = 0
	default_compilers = {'c': [['dcc', '-fsanitize=address'], ['dcc', '-fsanitize=valgrind']]}
	default_checkers = {'c': [['1521', 'c_check']], 's' : [['1521', 'mipsy', '--check']]}
"
parameters="
	default_compilers = {'c' : [['clang', '-Werror', '-std=gnu11', '-g', '-lm']]}
	upload_url = https://example.com/autotest.cgi
"

exec ./lemontest.py --exercise_directory tests --parameters "$parameters" "$@"
