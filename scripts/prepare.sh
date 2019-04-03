#!/usr/bin/env sh

set -e

__newline() {
    echo ''
}

__info() {
    echo "[INFO] $1"
}


cd "$(cd "$(dirname "$0")/.." && pwd -P)"
repodir="${PWD}"

__info "preparing repo-directory: ${repodir}"

__info 'preparing subdirectories...'
mkdir -v -p artifacts artifacts/config

__info 'checking out git-submodules...'
git submodule update --init --recursive

# check if sudo is required to run docker
docker info > /dev/null 2>&1 || sudocmd='sudo'

# build required docker-containers...
for image in alpine ansible pwdgen ssh-keygen ; do
    cd "${repodir}/eaas/ansible/docker/${image}"
    __info "building ${image} docker-container..."
    ${sudocmd} ./build-image.sh
    __newline
done

cd "${repodir}"

keydir='./artifacts/ssh'
key="${keydir}/admin.key"
if [ ! -e "${key}" ] ; then
    __info 'generating ssh-key...'
    mkdir -v -p "${keydir}"
    ${sudocmd} ./eaas/ansible/scripts/ssh-keygen.sh "${key}" 'admin@eaas'
fi

