
_is_backend=${1}
_branch_name=${2}

if ${_is_backend}  ; then
    _repo_url="https://gitlab.com/openslx/eaas-server.git"
else
    _repo_url="https://gitlab.com/openslx/demo-ui.git"
fi

_check_branch=$(git ls-remote --heads ${_repo_url} ${_branch_name})
if [[ -z ${_check_branch} ]]; then
    echo "master"
else
    echo "${_branch_name}"
fi