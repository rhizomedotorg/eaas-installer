#!/bin/sh -xeu

# HACK: python3-cryptography works around https://github.com/ansible/ansible/issues/73859
apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
  sudo \
  git docker.io unzip \
  python3-pip python3-cryptography \
  curl socat

DEBIAN_FRONTEND=noninteractive apt-get install -y python-is-python3 \
  || update-alternatives --install /usr/bin/python python /usr/bin/python3 100

. /etc/os-release

if [ "${NAME-}" = "Ubuntu" ] && [ "${VERSION_ID-}" = "24.04" ]; then
  DEBIAN_FRONTEND=noninteractive apt-get install -y docker-compose ansible-core
  exit
fi

break="--break-system-packages"
if [ "${NAME-}" = "Ubuntu" ] && [ "${VERSION_ID-}" = "22.04" ]; then
  break=""
fi

# HACK: make compatible to Python 3.11+
rm -f /usr/lib/python3.*/EXTERNALLY-MANAGED
pip3 install $break --no-build-isolation docker-compose "docker<7" ansible
pip3 install $break "urllib3<2"
