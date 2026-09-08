#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ "${1:-}" = "--preflight" ]; then
    python3 "$root/verify_manifest.py"
    python3 "$root/oracle.py"
    printf '%s\n' 'T-0191 status=preflight-only build=no simulation=no publication=no'
    exit 0
fi

if [ "${1:-}" = "--host-check" ]; then
    python3 "$root/verify_manifest.py"
    python3 "$root/oracle.py"
    env -i PATH="/usr/bin:/bin:/usr/sbin:/sbin" \
        python3 "$root/host_check.py"
    printf '%s\n' 'T-0191 status=host-check-only build=no simulation=no publication=no'
    exit 0
fi

if [ "${1:-}" = "--simulate" ]; then
    shift
    python3 "$root/run_authorized.py" "$@"
    exit 0
fi

printf '%s\n' 'T-0191 refused: choose --preflight, --host-check, or --simulate explicitly' >&2
exit 2
