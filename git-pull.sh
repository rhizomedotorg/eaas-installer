#!/usr/bin/env sh

set -e

remote="$1"
branch="$2"

test -z "${remote}" && remote='origin'
test -z "${branch}" && branch='master'

git fetch "${remote}" "${branch}"
git checkout "${branch}"
git submodule update --init --recursive
