#!/usr/bin/env sh

repodir="$(cd "$(dirname -- "$0")/.." && pwd -P)"

# should ansible be run in local mode?
if grep 'ansible_host: localhost' './artifacts/config/hosts.yaml' > /dev/null 2>&1 ; then
    if test "$(id -u)" != "0"; then
        set - '--ask-become-pass' "$@"
    fi
fi

set - '--verbose' \
      '--inventory' './artifacts/config/hosts.yaml' \
      '--extra-vars' '@./artifacts/config/eaasi.yaml' \
      "$@" \
      'deployment.yaml'

exec "${repodir}/scripts/ansible-runner.sh" \
    ansible-playbook "$@"
