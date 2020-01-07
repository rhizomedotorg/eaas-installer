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

if [ "$1" = '--local-mode' ] ; then
    echo "
In local-mode, the controller machine is also the installation target machine.
To be able to run the EaaSI-Installer locally, please first install an official
Ansible package by following the instructions for your Linux distribution.

For Ubuntu:
https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#latest-releases-via-apt-ubuntu

For RHEL and CentOS:
https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#latest-release-via-dnf-or-yum
"
    exit 0
fi

# build required docker-containers...
for image in alpine ansible pwdgen ssh-keygen ; do
    cd "${repodir}/eaas/ansible/docker/${image}"
    __info "building ${image} docker-container..."
    ./build-image.sh
    __newline
done

cd "${repodir}"

keydir='./artifacts/ssh'
key="${keydir}/admin.key"
if [ ! -e "${key}" ] ; then
    __info 'generating ssh-key...'
    mkdir -v -p "${keydir}"
    ./eaas/ansible/scripts/ssh-keygen.sh "${key}" 'eaas-admin'
fi
