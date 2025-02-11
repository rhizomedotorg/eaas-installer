#!/bin/sh -xeu

# HACK: python3-cryptography works around https://github.com/ansible/ansible/issues/73859
apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
  sudo \
  git docker.io unzip \
  python3-pip python3-cryptography \
  curl socat

DEBIAN_FRONTEND=noninteractive apt-get install -y python-is-python3 \
  || update-alternatives --install /usr/bin/python python /usr/bin/python3 100

# HACK: make compatible to Python 3.11+
rm -f /usr/lib/python3.*/EXTERNALLY-MANAGED
pip3 install --break-system-packages --no-build-isolation docker-compose "docker<7" ansible
pip3 install --break-system-packages "urllib3<2"
