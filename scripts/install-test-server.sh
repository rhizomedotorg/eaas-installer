#!/bin/sh -xeu
cd -- "$(dirname -- "$(realpath -- "$0")")/.."

: "${dry_run=}"
: "${setup_keycloak=}"
: "${eaas_ansible_repo=}"
: "${eaas_ansible_branch=}"
: "${docker_image_tag=}"
: "${https=}"
: "${acmesh=}"
: "${domain=}"

_not_dry() {
  if ! test "$dry_run"; then
    "$@"
  fi
}

# HACK: disable rsyslog, which regularly fills /var/log/messages with several gigabytes
_not_dry systemctl disable --now rsyslog || :

_not_dry ./scripts/install-dependencies.sh

if ! type yq; then
  curl -fL https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 |
    sudo install /dev/stdin /usr/local/bin/yq
fi

_not_dry ./scripts/prepare.sh --local-mode

(
  set --
  if test "$eaas_ansible_repo"; then
    set -- "$@" --reference "$eaas_ansible_repo"
  fi
  if test "$eaas_ansible_branch"; then
    set -- "$@" --branch "$eaas_ansible_branch"
  fi
  if test "$#" != 0; then
    git submodule update --remote "$@" eaas/ansible
  fi
)

hosts="config/localhost.yaml.template"
config="config/eaasi.yaml.template"

_not_dry ln -sr "$hosts" artifacts/config/hosts.yaml
_not_dry ln -sr "$config" artifacts/config/eaasi.yaml

update=""
if ! test "$dry_run"; then
  update="-i"
fi

yq $update '
  .all.hosts.eaas-gateway.ansible_user = "root"
  | with(select(strenv(https) != "");
    .all.hosts.eaas-gateway.eaas_hostname = strenv(domain))
' "$hosts"

yq $update '
  .host.eaas_service_name = "eaas"
  | with(select(strenv(docker_image_tag) != "");
    .docker.image = strenv(docker_image_tag))
  | with(select(strenv(https) != "");
    .docker.port = 443 |
    .docker.ssl = {
      "enabled": true,
      "certificate": "./artifacts/ssl/certificate.crt",
      "private_key": "./artifacts/ssl/private.key"
    })
  | with(select(strenv(setup_keycloak) != "");
    .eaas.enable_user_auth = true
    | .eaas.enable_devmode = true
    | .keycloak = {
      "enabled": true,
      "admin_user": "admin",
      "admin_password": "admin"}
    | with(select(strenv(https) == "");
      .keycloak.frontend_url = "http://localhost:8080/auth")
    | with(select(strenv(https) != "");
      .keycloak.frontend_url = "https://" + strenv(domain) + "/auth")
  )
' "$config"

if ! test "$dry_run" && test "$acmesh" && test "$domain"; then
  export HOME=/root
  curl https://get.acme.sh | sh

  # Buypass will issue a certificate valid for 180 days.
  # See: https://github.com/acmesh-official/acme.sh/wiki/Server
  #
  # Use webmaster@$domain as generic email address as it is
  # used by both https://www.rfc-editor.org/rfc/rfc2142 and
  # https://github.com/cabforum/servercert/blob/main/docs/BR.md#32244-constructed-email-to-domain-contact
  ~/.acme.sh/acme.sh --standalone --issue --domain "$domain" --email "webmaster@$domain" --server buypass

  mkdir -p artifacts/ssl
  ln -sr "$HOME/.acme.sh/$domain"*"/$domain.key" artifacts/ssl/private.key
  ln -sr "$HOME/.acme.sh/$domain"*"/fullchain.cer" artifacts/ssl/certificate.crt
fi

_not_dry ./scripts/deploy.sh
_not_dry chmod -R ugo=u /eaas-home
