#!/usr/bin/env sh

set -e

repodir="$(cd "$(dirname -- "$0")/.." && pwd -P)"
workdir='/var/work'

exec docker run --rm --tty --interactive --name eaas-ansible \
    --volume "${repodir}:${workdir}" \
    --workdir "${workdir}" \
    eaas/ansible \
    "$@"
