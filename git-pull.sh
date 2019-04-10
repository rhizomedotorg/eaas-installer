#!/usr/bin/env sh

remote="$1"
branch="$2"

test -z "${remote}" && remote='origin'
test -z "${branch}" && branch='master'

git pull "${remote}" "${branch}"
git submodule update --recursive