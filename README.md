# Description

This repository contains an automated installer for the EaaSI project.


## Prepare Controller-Machine

The installer is implemented using Docker and Ansible. It is assumed, that Docker
is already installed and configured. To prepare Ansible controller-machine from
which the installation process will be coordinated, run:
```
$ ./scripts/prepare.sh
```

This will clone required Git submodules, build Docker images and generate new
SSH key-pair to access the installation target machine.

Copy generated SSH public key to the installation target machine:
```
$ ssh-copy-id -i ./artifacts/ssh/admin.key user@hostname
```


### Local-Mode

If you want to use the controller-machine as an installation target for some
reason, then the controller-machine should be prepared in *local-mode* instead:
```
$ ./scripts/prepare.sh --local-mode
```


## Configure EaaSI-Installer

The target machines to install EaaSI on must be defined in `./artifacts/config/hosts.yaml`.
You can use provided template file as an example:
```
$ cp ./config/hosts.yaml.template ./artifacts/config/hosts.yaml
```

If *local-mode* option was choosen in the previous step, the following template
should be used instead:
```
$ cp ./config/localhost.yaml.template ./artifacts/config/hosts.yaml
```

EaaSI deployment configuration must be defined in `./artifacts/config/eaasi.yaml`.
For a basic configuration, you can use provided template file:
```
$ cp ./config/eaasi.yaml.template ./artifacts/config/eaasi.yaml
```


## Run EaaSI-Installer

When everything is configured, the installation process can be started by running:
```
$ ./scripts/deploy.sh
```
