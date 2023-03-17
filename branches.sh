#!/bin/bash
_is_backend=${1}
_branch_name=${2}

if test "${_is_backend}"  = "true"  ; then
    _repo_url="https://gitlab.com/emulation-as-a-service/eaas-server.git"
else
    _repo_url="https://gitlab.com/emulation-as-a-service/demo-ui"
fi

_check_branch=$(git ls-remote --heads ${_repo_url} ${_branch_name})
if [[ -z ${_check_branch} ]]; then
    echo "master"
else
    echo "${_branch_name}"
fi