#!/bin/sh -xeu
cd -- "$(dirname -- "$(realpath -- "$0")")/.."

: "${setup_keycloak=}"
: "${eaas_ansible_repo=}"
: "${eaas_ansible_branch=}"
: "${docker_image_tag=}"
: "${https=}"
: "${acmesh=}"
: "${domain=}"

# HACK: disable rsyslog, which regularly fills /var/log/messages with several gigabytes
systemctl disable --now rsyslog || :

./scripts/install-dependencies.sh
./scripts/prepare.sh --local-mode

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

ln -sr "$hosts" artifacts/config/hosts.yaml
ln -sr "$config" artifacts/config/eaasi.yaml

sed -i 's/<local-user>/root/g' "$hosts"
sed -i 's/eaas_service_name: "eaas-local"/eaas_service_name: "eaas"/g' "$config"

if test "$docker_image_tag"; then
  sed -i 's/image: "eaas\/eaas-appserver"/image: "eaas\/eaas-appserver:'"$docker_image_tag"'"/' "$config"
fi

if test "$https" && test "$domain"; then
  cat >> "$hosts" << EOF
      eaas_hostname: $domain
EOF
  sed -i 's/port: 8080/port: 443/' "$config"
  sed -i '/#ssl:/s/#//' "$config"
  sed -i '/#  enabled/s/#//' "$config"
fi

if test "$acmesh" && test "$domain"; then
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
  sed -Ei '/#  certificate:/s/#//' "$config"
  sed -Ei '/#  private_key:/s/#//' "$config"
  ln -sr "$HOME/.acme.sh/$domain/$domain.key" artifacts/ssl/private.key
  ln -sr "$HOME/.acme.sh/$domain/fullchain.cer" artifacts/ssl/certificate.crt
fi

if test "$setup_keycloak"; then
frontend_url="http://localhost:8080/auth"
if test "$https"; then
  frontend_url="https://$domain/auth"
fi
cat >> "$config" << EOF

keycloak:
  enabled: true
  frontend_url: "$frontend_url"
  admin_user: admin
  admin_password: admin
EOF
sed -i '/^eaas:/a\  enable_user_auth: true' "$config"
fi

./scripts/deploy.sh
chmod -R ugo=u /eaas-home
