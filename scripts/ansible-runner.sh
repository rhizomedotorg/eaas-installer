#!/usr/bin/env sh

set -e

repodir="$(cd "$(dirname -- "$0")/.." && pwd -P)"
workdir='/var/work'

# check if sudo is required to run docker
docker info > /dev/null 2>&1 || sudocmd='sudo'

exec ${sudocmd} docker run --rm --tty --interactive --name eaas-ansible \
    --volume "${repodir}:${workdir}" \
    --workdir "${workdir}" \
    eaas/ansible \
    "$@"
