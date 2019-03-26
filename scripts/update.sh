#!/usr/bin/env sh

__components_as_json() {
    # convert a list of space-separated strings
    # to a JSON object containing an array
    echo -n '{"eaas_update_components":["'
    echo -n "$@" | sed 's/ /","/g'
    echo -n '"]}'
}

repodir="$(cd "$(dirname -- "$0")/.." && pwd -P)"

if [ "$#" -eq 0 ] ; then
    # no user-specified components, update all
    set - 'ui' 'ear' 'docker-image'
fi

exec "${repodir}/scripts/deploy.sh" \
    '--extra-vars' "$(__components_as_json "$@")"
