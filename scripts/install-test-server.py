#!/usr/bin/env python3

import os
import subprocess
import functools
import yaml


def cmd(*args, **kwds):
    print("would run" if dry_run else "running", args, kwds, "...")
    if dry_run:
        return subprocess.run("true")
    return subprocess.run(args, **{"check": True, **kwds})


def yaml_load(path):
    with open(path) as file:
        return yaml.safe_load(file)


def yaml_save(path, obj):
    string = yaml.safe_dump(obj, sort_keys=False)
    print(f"{path}:\n{string}")
    if not dry_run:
        with open(path, "w") as file:
            file.write(string)


print = functools.partial(print, flush=True)

os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/..")

dry_run = bool(os.environ.get("dry_run"))
setup_keycloak = bool(os.environ.get("setup_keycloak"))
eaas_ansible_repo = os.environ.get("eaas_ansible_repo")
eaas_ansible_branch = os.environ.get("eaas_ansible_branch")
docker_image_tag = os.environ.get("docker_image_tag")
https = os.environ.get("https")
acmesh = os.environ.get("acmesh")
domain = os.environ.get("domain")

eaas_server_ear_url = os.environ.get("eaas_server_ear_url")
ui_artifact_url = os.environ.get("ui_artifact_url")


# HACK: disable rsyslog, which regularly fills /var/log/messages with several gigabytes
cmd("systemctl", "disable", "--now", "rsyslog", check=False)

cmd("./scripts/install-dependencies.sh")
cmd("./scripts/prepare.sh", "--local-mode")


def update_git():
    update = False

    if eaas_ansible_repo:
        update = True
        cmd("git", "submodule", "set-url", "--",
            "eaas/ansible", eaas_ansible_repo)

    if eaas_ansible_branch:
        update = True
        cmd("git", "submodule", "set-branch", "--branch",
            eaas_ansible_branch, "--", "eaas/ansible")

    if update:
        cmd("git", "submodule", "update", "--remote", "eaas/ansible")


update_git()

hosts = yaml_load("config/localhost.yaml.template")
config = yaml_load("config/eaasi.yaml.template")

cmd("ln", "-sr", "config/localhost.yaml.template", "artifacts/config/hosts.yaml")
cmd("ln", "-sr", "config/eaasi.yaml.template", "artifacts/config/eaasi.yaml")

hosts["all"]["hosts"]["eaas-gateway"]["ansible_user"] = "root"
if https:
    hosts["all"]["hosts"]["eaas-gateway"]["eaas_hostname"] = domain

config["host"]["eaas_service_name"] = "eaas"

config["coturn"] = {
    "enabled": True,
}

if docker_image_tag:
    config["docker"]["image"] = docker_image_tag

if https:
    config["docker"]["port"] = 443
    config["docker"]["ssl"] = {
        "enabled": True,
        "certificate": "./artifacts/ssl/certificate.crt",
        "private_key": "./artifacts/ssl/private.key",
    }

if setup_keycloak:
    config["eaas"]["enable_user_auth"] = True
    config["eaas"]["enable_backend_auth"] = True
    config["eaas"]["enable_devmode"] = True
    config["keycloak"] = {
        "enabled": True,
        "admin_user": "admin",
        "admin_password": "admin",
    }
    if https:
        config["keycloak"]["frontend_url"] = f"https://{domain}/auth"
    else:
        config["keycloak"]["frontend_url"] = f"http://localhost:8080/auth"

if acmesh:
    os.environ["HOME"] = "/root"
    cmd("curl https://get.acme.sh | sh", shell=True)

    # Buypass will issue a certificate valid for 180 days.
    # See: https://github.com/acmesh-official/acme.sh/wiki/Server
    #
    # Use webmaster@$domain as generic email address as it is
    # used by both https://www.rfc-editor.org/rfc/rfc2142 and
    # https://github.com/cabforum/servercert/blob/main/docs/BR.md#32244-constructed-email-to-domain-contact
    cmd(os.path.expanduser("~/.acme.sh/acme.sh"), "--standalone", "--issue",
        "--domain", domain, "--email", f"webmaster@{domain}", "--server", "buypass")

    cmd("mkdir", "-p", "artifacts/ssl")
    cmd('ln -sr -- "$HOME/.acme.sh/$0"*"/$0.key" artifacts/ssl/private.key',
        domain, shell=True)
    cmd('ln -sr -- "$HOME/.acme.sh/$0"*"/fullchain.cer" artifacts/ssl/certificate.crt',
        domain, shell=True)

if eaas_server_ear_url:
    config["eaas_server_ear_url"] = eaas_server_ear_url
if ui_artifact_url:
    config["ui_artifact_url"] = ui_artifact_url

print("Hosts:", hosts)
print("Config:", config)

yaml_save("artifacts/config/hosts.yaml", hosts)
yaml_save("artifacts/config/eaasi.yaml", config)

cmd("./scripts/deploy.sh")
cmd("chmod", "-R", "ugo=u", "/eaas-home")
