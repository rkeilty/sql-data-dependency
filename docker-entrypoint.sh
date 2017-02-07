#!/bin/bash
set -eo pipefail

# if command starts with an option, prepend sqldd
if [ "${1:0:1}" = '-' ]; then
	set -- sqldd "$@"
fi

exec "$@"
