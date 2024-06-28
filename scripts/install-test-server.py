#!/usr/bin/env python3

import functools
import glob
import os
import pathlib
import shlex
import subprocess
from urllib.parse import urlparse, urlunparse, quote

import yaml


def cmd(*args, **kwds):
    print("would run" if dry_run else "running", f"`{shlex.join(args)}`", kwds, "...")
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


def load_source(name, pathname):
    from importlib.machinery import SourceFileLoader
    from importlib.util import module_from_spec, spec_from_loader

    loader = SourceFileLoader(name, pathname)
    module = module_from_spec(spec_from_loader(name, loader))
    loader.exec_module(module)
    return module


def retry(fn, tries):
    for i in range(tries):
        try:
            return fn()
        except:
            if i == tries - 1:
                raise


print = functools.partial(print, flush=True)

wd = os.getcwd()
os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/..")

dry_run = bool(os.environ.get("dry_run"))
setup_keycloak = bool(os.environ.get("setup_keycloak"))
eaas_ansible_repo = os.environ.get("eaas_ansible_repo")
eaas_ansible_branch = os.environ.get("eaas_ansible_branch")
docker_image_tag = os.environ.get("docker_image_tag")
eaasi_ui_version = os.environ.get("eaasi_ui_version")
https = os.environ.get("https")
acmesh = os.environ.get("acmesh")
domain = os.environ.get("domain")
wait_for_eaas_server = os.environ.get("wait_for_eaas_server")
import_test_environments = os.environ.get("import_test_environments")
show_summary = os.environ.get("show_summary")

if import_test_environments or show_summary:
    wait_for_eaas_server = "1"

eaas_server_ear_url = os.environ.get("eaas_server_url")
ui_artifact_url = os.environ.get("eaas_ui_url")
eaas_version = os.environ.get("eaas_version")
demo_ui_version = os.environ.get("demo_ui_version")

print("All env variables in python:", os.environ)

# HACK: disable rsyslog, which regularly fills /var/log/messages with several gigabytes
try:
    cmd("systemctl", "disable", "--now", "rsyslog")
except:
    pass

cmd("./scripts/install-dependencies.sh")
cmd("./scripts/prepare.sh", "--local-mode")


def update_git():
    update = False

    if eaas_ansible_repo:
        update = True
        cmd("git", "submodule", "set-url", "--", "eaas-ansible", eaas_ansible_repo)

    if eaas_ansible_branch:
        update = True
        cmd(
            "git",
            "submodule",
            "set-branch",
            "--branch",
            eaas_ansible_branch,
            "--",
            "eaas-ansible",
        )

    if update:
        cmd("git", "submodule", "sync", "eaas/ansible")
        cmd("git", "submodule", "update", "--remote", "eaas/ansible")


def handle_artifacts(artifact_url_path, artifact_type):
    if artifact_url_path:
        print(f"{artifact_type} was provided:")
        if not urlparse(artifact_url_path).scheme:
            artifact_url_path = pathlib.Path(wd, artifact_url_path).resolve().as_uri()
            print(f"--- {artifact_type} was provided as a path, not as URL")
        else:
            print(f"--- {artifact_type} was provided as URL.")

        print(f"Using {artifact_type}:", artifact_url_path)
        config[artifact_type] = artifact_url_path

    else:
        print(f"No {artifact_type} was provided. Defaulting to latest HEAD build.")


update_git()

hosts = yaml_load("config/localhost.yaml.template")
config = yaml_load("config/local-mode.yaml.template")

cmd("ln", "-sr", "config/localhost.yaml.template", "artifacts/config/hosts.yaml")
cmd("ln", "-sr", "config/local-mode.yaml.template", "artifacts/config/eaasi.yaml")

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
        "admin_user": "superadmin",
        "admin_password": "superadmin",
    }
    if https:
        config["keycloak"]["frontend_url"] = f"https://{domain}/auth"
    else:
        config["keycloak"]["frontend_url"] = f"http://localhost:8080/auth"

if acmesh:
    if acmesh in {"1", "true"}:
        acmesh = "buypass"

    os.environ["HOME"] = "/root"
    cmd("curl https://get.acme.sh | sh", shell=True)

    # Buypass will issue a certificate valid for 180 days.
    # See: https://github.com/acmesh-official/acme.sh/wiki/Server
    #
    # Use webmaster@$domain as generic email address as it is
    # used by both https://www.rfc-editor.org/rfc/rfc2142 and
    # https://github.com/cabforum/servercert/blob/main/docs/BR.md#32244-constructed-email-to-domain-contact
    #
    # Retry if acme.sh fails as some ACME providers are not very reliable.
    retry(
        lambda: cmd(
            os.path.expanduser("~/.acme.sh/acme.sh"),
            "--standalone",
            "--issue",
            "--domain",
            domain,
            "--email",
            f"webmaster@{domain}",
            "--server",
            acmesh,
        ),
        5,
    )

    cmd("mkdir", "-p", "artifacts/ssl")
    cmd(
        'ln -sr -- "$HOME/.acme.sh/$0"*"/$0.key" artifacts/ssl/private.key',
        domain,
        shell=True,
    )
    cmd(
        'ln -sr -- "$HOME/.acme.sh/$0"*"/fullchain.cer" artifacts/ssl/certificate.crt',
        domain,
        shell=True,
    )

handle_artifacts(eaas_server_ear_url, "eaas_server_ear_url")
handle_artifacts(ui_artifact_url, "ui_artifact_url")

if eaas_version:
    config["eaas"]["version"] = eaas_version
if demo_ui_version:
    config["demo_ui"]["version"] = demo_ui_version

if eaasi_ui_version:
    config.setdefault("eaasi_ui", {})["version"] = eaasi_ui_version
    # HACK: see https://gitlab.com/eaasi/eaasi-installer/-/blob/1a3a7a9de722bafc42e75079a7aa2c2357c95dc4/config/eaasi.yaml.template#L39-45
    config["eaas"] |= {
        "enable_backend_auth": True,
        "enable_user_auth": True,
        "single_user_mode": False,
        "user_archive_enabled": False,
        "auth_audience": "",
    }

print("Hosts:", hosts)
print("Config:", config)

yaml_save("artifacts/config/hosts.yaml", hosts)
yaml_save("artifacts/config/eaasi.yaml", config)

# HACK: for check=False, see https://gitlab.com/emulation-as-a-service/eaas-installer/-/issues/6
cmd("./scripts/deploy.sh", check=False)
cmd("chmod", "-R", "ugo=u", "/eaas-home")

auth = ""
if setup_keycloak:
    docker_compose = yaml_load(glob.glob("/eaas*/docker-compose.yaml")[0])
    environment = docker_compose["services"]["keycloak"]["environment"]
    user = environment.get("KEYCLOAK_ADMIN") or environment["KEYCLOAK_USER"]
    password = (
        environment.get("KEYCLOAK_ADMIN_PASSWORD") or environment["KEYCLOAK_PASSWORD"]
    )
    auth = f"{user}:{password}@"

url = f"http://{auth}localhost:{config['docker']['port']}"
if https:
    url = f"https://{auth}{domain}:{config['docker']['port']}"

if wait_for_eaas_server:
    cmd(
        'while ! curl -f "$0"; do sleep 10; done',
        f"{url}/emil/admin/build-info",
        shell=True,
    )

if setup_keycloak:
    # HACK: make temporary password permanent
    cmd("sed", "-i", "/'temporary': True/d", "scripts/eaas-orgctl/eaas-orgctl")
    eaas_orgctl = load_source("eaas_orgctl", "scripts/eaas-orgctl/eaas-orgctl")

    url_parsed = urlparse(url)
    url_parsed = url_parsed._replace(netloc=url_parsed.netloc.split("@")[-1])
    keycloak_url = urlunparse(url_parsed)
    keycloak = eaas_orgctl.Keycloak(keycloak_url, user, password)
    keycloak_user = keycloak.fetch_user(user)
    keycloak.assign_client_role(keycloak_user["id"], "eaas-admin")

    groupadmin = eaas_orgctl.User(
        "admin", "groupadmin@eaas.test", "group", "admin", "eaas-admin"
    )
    groupadmin.password = "admin"
    # HACK: allow to specify constant password
    groupadmin.randomize_password = lambda: None
    keycloak.create_organization(eaas_orgctl.Organization("group", "group", groupadmin))

    url_parsed = url_parsed._replace(
        netloc=f"{quote(groupadmin.username, safe='')}:{quote(groupadmin.password, safe='')}@{url_parsed.netloc}"
    )
    url = urlunparse(url_parsed)

if import_test_environments:
    cmd("git", "clone", "--recurse-submodules", "https://eaas.dev/eaas-client")
    cmd("eaas-client/contrib/cli/install-deno")
    cmd("eaas-client/contrib/cli/import-tests", url)

if show_summary:
    cmd(
        "git",
        "clone",
        "--recurse-submodules",
        "https://eaas.dev/eaas-debug",
        "/eaas-debug",
    )

    cmd("/eaas-debug/show-summary")
