#!/usr/bin/env sh

repodir="$(cd "$(dirname -- "$0")/.." && pwd -P)"

set - '--verbose' \
      '--inventory' './artifacts/config/hosts.yaml' \
      '--extra-vars' '@./artifacts/config/eaasi.yaml' \
      "$@" \
      'deployment.yaml'

exec "${repodir}/scripts/ansible-runner.sh" \
    ansible-playbook "$@"
