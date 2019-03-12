#!/usr/bin/env sh

repodir="$(cd "$(dirname -- "$0")/.." && pwd -P)"

# user-provided args available?
if [ "$#" -eq 0 ] ; then
    # no, use defaults
    set - '--verbose' \
          '--inventory' './artifacts/config/hosts.yaml' \
          '--extra-vars' '@./artifacts/config/eaasi.yaml' \
          'deployment.yaml'
fi

exec "${repodir}/scripts/ansible-runner.sh" \
    ansible-playbook "$@"
