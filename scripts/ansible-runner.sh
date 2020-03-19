#!/usr/bin/env sh

set -e

repodir="$(cd "$(dirname -- "$0")/.." && pwd -P)"
workdir='/var/work'

cd "${repodir}"

# should ansible be run in local mode?
if grep 'ansible_host: localhost' './artifacts/config/hosts.yaml' > /dev/null 2>&1 ; then
    exec "$@"
fi

# check if sudo is required to run docker
docker info > /dev/null 2>&1 || sudocmd='sudo'

exec ${sudocmd} docker run --rm --tty --interactive --name eaas-ansible \
    --volume "${repodir}:${workdir}" \
    # --net=host \ # uncomment if using VPN
    --workdir "${workdir}" \
    eaas/ansible \
    "$@"
