#!/bin/sh

parameters="
	default_compilers = {'c' : [['clang', '-Werror', '-std=gnu11', '-g', '-lm']]}
	upload_url = https://example.com/autotest.cgi
"

exec ../lemontest.py --exercise_directory . --parameters "$parameters" "$@"