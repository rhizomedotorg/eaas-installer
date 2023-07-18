#!/usr/bin/env python3

import argparse
import base64
import datetime
import glob
import os
import pathlib
import re
import shlex
import subprocess
from shlex import quote

# sudo apt install python3-openstacksdk
import openstack


def nonone(fn, *args, **kwds):
    return fn(*args, **{k: v for k, v in kwds.items() if v is not None})


def parse_env(env_strings):
    return {k: v for k, v in (l.split("=", 2) for l in env_strings)}


def create():
    image = next(
        filter(
            lambda v: re.search(r"(?i)(?<!baremetal - )ubuntu 20.04", v.name),
            conn.list_images(),
        )
    )
    flavor = conn.compute.find_flavor(args.flavor)
    network = conn.network.find_network(args.network)

    set_env = shlex.join(["export", *map("=".join, parse_env(args.env).items())])

    ssh_keys = pathlib.Path(args.ssh_key_file).read_text() if args.ssh_key_file else ""

    name = f"{args.prefix}{datetime.datetime.utcnow().isoformat()}Z{''.join(f' {v}' for v in args.env)}"

    cloud_config = rf"""
#!/bin/sh
{set_env}

export domain="$(cat /var/lib/cloud/data/instance-id)."{quote(args.domain)}
hostnamectl set-hostname -- "${{domain%%-*}}"
hostnamectl set-hostname --pretty -- "https://$domain "{quote(name)}

printf "%s\n" {quote(ssh_keys)} >> /home/ubuntu/.ssh/authorized_keys
curl -fL https://github.com/emulation-as-a-service/cloud-init-update/raw/main/user-data | sh
apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y git

git clone {
      f'--branch {quote(args.installer_branch)}' if args.installer_branch else ""
    } --recursive https://gitlab.com/emulation-as-a-service/eaas-installer
eaas-installer/scripts/install-test-server.py

curl -fsSL https://deno.land/x/install/install.sh | DENO_INSTALL=/usr/local sh

auth="$(python3 -c 'print(__import__("yaml").safe_load(open(__import__("glob").glob("/eaas*/docker-compose.yaml")[0]))["services"]["keycloak"]["environment"]["KEYCLOAK_USER"])')"
if test "$auth"; then
  auth="admin:$auth@"
fi

if test "${{https-}}"; then
  url="https://${{auth}}$domain"
else
  url="http://${{auth}}localhost"
fi

while ! curl -f "$url/emil/admin/build-info"; do sleep 10; done

git clone --rec https://eaas.dev/eaas-client
eaas-client/contrib/cli/import-tests "$url"

git clone --rec https://eaas.dev/eaas-debug /eaas-debug
""".lstrip()

    server = nonone(
        conn.compute.create_server,
        name=name,
        image_id=image.id if not args.volume_size else None,
        flavor_id=flavor.id,
        networks=[{"uuid": network.id}] if network else [],
        user_data=base64.b64encode(cloud_config.encode()).decode(),
        key_name=args.ssh_key_pair,
        security_groups=[{"name": args.security_group}]
        if args.security_group
        else None,
        block_device_mapping_v2=[
            {
                "boot_index": 0,
                "uuid": image.id,
                "source_type": "image",
                "volume_size": args.volume_size,
                "destination_type": "volume",
                "delete_on_termination": True,
                "disk_bus": "virtio",
            }
        ]
        if args.volume_size
        else None,
    )

    server = conn.compute.wait_for_server(server)

    hostname = f"{server.id}.{args.domain}"
    ip = next(filter(lambda v: v.version == 4, conn.compute.server_ips(server))).address

    if not args.no_dns:
        if not os.path.exists("external-dns"):
            subprocess.run(
                [
                    'curl -fL "$0" | install /dev/stdin external-dns',
                    "https://gitlab.com/emulation-as-a-service/external-dns-util/-/jobs/artifacts/HEAD/raw/external-dns?job=build",
                ],
                shell=True,
                check=True,
            )
        hostname_parts = hostname.split(".")
        while hostname_parts:
            token_path = pathlib.Path(f"dns_{'.'.join(hostname_parts)}/token")
            if token_path.exists():
                break
            hostname_parts.pop(0)
        env = parse_env(token_path.read_text().rstrip().split("\n"))

        subprocess.run(
            ["./external-dns", "add", hostname, "A", ip],
            env={**os.environ, **env},
            check=True,
        )

    print(info(name, hostname))


def info(name, hostname):
    return f"""
{name}
ssh ubuntu@{hostname}
ssh -L 8080:localhost:8080 ubuntu@{hostname}
https://{hostname}/admin
""".lstrip()


def list_servers():
    servers = conn.list_servers()
    servers.sort(key=lambda server: server.name)
    servers = [server for server in servers if server.name.startswith(args.prefix)]

    for server in servers:
        if args.debug:
            print(server)
        hostname = f"{server.id}.{args.domain}"
        print(info(server.name, hostname))
    return servers


def cleanup():
    servers = list_servers()
    if not args.prefix:
        raise ValueError("prefix must not be empty for cleanup")
    for server in servers[: -args.keep] if args.keep != 0 else servers:
        print(f"Deleting {server.id}.{args.domain} ({server.name})...")
        if not args.dry_run:
            conn.compute.delete_server(server)


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", action="store_true", help="enable debug output")
parser.add_argument(
    "-c",
    "--cloud",
    default="openstack",
    help='cloud to create a VM in (see "clouds" object in clouds.yaml, which can be generated using OpenStack Dashboard > Identity > Application Credentials > Create Application Credential > Download clouds.yaml)',
)
parser.add_argument(
    "-d",
    "--domain",
    help="domain under which to create a new hostname for the VM (the VM's hostname will be $uuid.$domain)",
)
parser.add_argument(
    "-p",
    "--prefix",
    help="prefix string to start/filter VM names with",
    default="eaas-test ",
)
subparsers = parser.add_subparsers(required=True)
subparser = subparsers.add_parser(
    "list", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
subparser.set_defaults(func=list_servers)
subparser = subparsers.add_parser(
    "cleanup", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
subparser.set_defaults(func=cleanup)
subparser.add_argument(
    "-n", "--dry-run", action="store_true", help="do not execute actions"
)
subparser.add_argument(
    "-k",
    "--keep",
    default=1,
    type=int,
    help="delete all but this many test server VMs",
)
subparser = subparsers.add_parser(
    "create", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
subparser.set_defaults(func=create)
subparser.add_argument("-f", "--flavor", default="d2-2", help="OpenStack flavor name")
subparser.add_argument(
    "-n", "--network", default="Ext-Net", help="OpenStack network name"
)
subparser.add_argument("-g", "--security-group", help="OpenStack security group name")
subparser.add_argument(
    "-v",
    "--volume-size",
    help="size of volume to create for VM (in GB) if explicit volume shall be created",
    type=int,
)
subparser.add_argument("--ssh-key-pair", help="OpenStack SSH key pair name")
subparser.add_argument(
    "-s", "--ssh-key-file", help="path to local file with SSH keys to inject into VM"
)
subparser.add_argument(
    "--no-dns",
    action="store_true",
    help="do not create A record for VM in DNS (A record must be provisioned by cloud provider)",
)
subparser.add_argument(
    "--installer-branch", help="branch of https://eaas.dev/eaas-installer to use on VM"
)
subparser.add_argument(
    "env",
    nargs="*",
    default=["https=1", "acmesh=1", "setup_keycloak=1"],
    help="environment variables (key=value) to set for eaas-installer on VM (see `scripts/install-test-server.py`). Example: https=1 acmesh=1 setup_keycloak=1 eaas_ansible_branch=HEAD",
)

args = parser.parse_args()

if args.debug:
    openstack.enable_logging(debug=True)

conn = openstack.connect(cloud=args.cloud)

if not args.domain:
    args.domain = conn.config.config.get("domain")

args.func()
