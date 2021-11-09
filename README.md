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


Please note: *local-mode* deployment is only supported with the Demo-UI. The EaaSI-UI
is not designed for and will not work predictably with a local-mode deployment.
See [below](#ui-deployment)


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

### UI Deployment

Two interfaces for the EaaSI stack are currently available via the `eaasi-installer`.
There is the ["Demo-UI"](https://eaasi.gitlab.io/eaasi_user_handbook/legacy/dev_ui.html)
(stable, newer EaaS platform features potentially available), and the "EaaSI-UI"
(newer design and UX, experimental state).

UI configuration options are defined in the `./artifacts/config/eaasi.yaml` - options in
the `demo_ui` section are for the Demo-UI, and options in the `eaasi_ui` section are for
the EaaSI-UI.

The two interfaces are not designed to run side-by-side. It is highly recommended to select
one and comment out the configuration for the other in your `./artifacts/config/eaasi.yaml`.

Please consult the [Handbook](https://eaasi.gitlab.io/eaasi_user_handbook/index.html) for
more detail on visual and functional differences between the two interfaces.


## Run EaaSI-Installer

When everything is configured, the installation process can be started by running:
```
$ ./scripts/deploy.sh
```
