#!/usr/bin/env sh

__components_as_json() {
    # convert a list of space-separated strings
    # to a JSON object containing an array
    local components="$(echo "$@" | sed 's/ /","/g')"
    printf '{"eaas_update_components":["%s"]}' "${components}"
}

repodir="$(cd "$(dirname -- "$0")/.." && pwd -P)"

if [ "$#" -eq 0 ] ; then
    # no user-specified components, update all
    set - 'ui' 'ear' 'docker-image'
fi

exec "${repodir}/scripts/deploy.sh" \
    '--extra-vars' "$(__components_as_json "$@")"
