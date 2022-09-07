#!/usr/bin/env sh

set -e

remote="$1"
branch="$2"

test -z "${remote}" && remote='origin'
test -z "${branch}" && branch='master'

__newline() {
	echo ''
}

__info() {
	echo "--> $1"
}

git fetch --tags "${remote}" "${branch}"
__newline

if git tag --list | grep --quiet "${branch}"; then
	__info 'Checking out remote tag...'
	git -c 'advice.detachedHead=false' checkout -f "${branch}"
else
	__info 'Checking out remote branch...'
	git checkout -B "${branch}" "${remote}/${branch}"
fi

__newline
__info 'Checking out submodules...'
git submodule update --init --recursive

__newline
__info "DONE: Version ${branch} checked out!"
