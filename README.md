[![Installation test](https://github.com/emulation-as-a-service/eaas-installer/actions/workflows/test.yml/badge.svg)](https://github.com/emulation-as-a-service/eaas-installer/actions/workflows/test.yml)

# EaaS Local-Mode Installation

This installer is able to deploy EaaS on a local computer (localhost) for testing / experiments.  This documentation is based on the EaaS-CI test runner (https://gitlab.com/emulation-as-a-service/experiments/eaas-ci-test).  

- This will work on Linux and Mac OSX. Other OS might work, but untested.
- By default EaaS will be installed as a systemd service and requires Docker to be installed as a systemd service as well.
- The EaaS interface will be accessible at `http://localhost:80`.

## Preconditions

The host system requires the following tools installed:

- A current [Docker](https://docs.docker.com/install/) version
- Python (v3 preferred) and Python PIP  

On a current Ubuntu just run
```
apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
  sudo \
  git docker.io unzip \
  python3-pip python-is-python3 \
  curl
```

(On Ubuntu 18.04, due to an [outdated version of pip](https://pythonspeed.com/articles/upgrade-pip/), you have to install `apt-get install -y python3-cryptography` or Ansible [will not install](https://github.com/ansible/ansible/issues/73859). Also, the `python-is-python3` package is not available, instead run `update-alternatives --install /usr/bin/python python /usr/bin/python3 100`.)

Finally, install python dependencies via Python PIP:
   ```bash
   sudo pip3 install docker-compose ansible
   ```
   
## Base Installation and Setup

The installation process is based on an Ansible *playbook*, a set of scripts that make changes to the computer's configuration based on parameters in a bunch of yaml files. Some of these parameters need to be tweaked depending on local requirements.

The installation process is supposed to run only once. To update the setup with new versions of EaaS, a separate updater is used.

1. Clone this repository e.g.
   ```bash
   git clone https://gitlab.com/emulation-as-a-service/eaas-local-installer.git
   cd eaas-local-installer
   ```

2. Run the preparation script and specify that you want to install locally:
	 ```bash
   ./scripts/prepare.sh --local-mode
   ```

3. Configure and customize your installation
   ```bash
   cp ./config/localhost.yaml.template ./artifacts/config/hosts.yaml
   cp ./config/eaasi.yaml.template ./artifacts/config/eaasi.yaml
   ```

4. Make changes to `artifacts/config/hosts.yaml`
     ```yaml
     ---
     all:
       hosts:
         eaas-gateway:
           ansible_user: eaas-user  ## change to your local username.
           ansible_host: localhost
           ansible_connection: local
     ```

**Note:** `ansible_user` needs to exist and requires sudo capabilities. 

5. Make changes to `artifacts/config/eaasi.yaml`:
    ```yaml
    ---
    host:
      build_dir: "/eaas-build" ## Set up target directories
      eaas_home: "/eaas-home"  ## on a drive with lots of space!
      eaas_service_name: "eaas-local" ## on systemd capable systems (e.g. ubuntu) a service unit will be created

    docker:
      image: "eaas/eaas-appserver"
      port: 80	# Cannot be 8080, see https://gitlab.com/emulation-as-a-service/eaas-ansible/-/issues/5

    ui:
      git_branch: "master"
      enable_network_sessions: true
      enable_containers: true
      enable_webrtc: true
      standalone: true
    
    eaas:
      git_branch: "master"
      enable_oaipmh_provider: true
      db_upgrade: true

    ```
6. Run `./scripts/deploy.sh` — after a few minutes, you should have your very own EaaS node running on your computer.

**Note:** If you have an older version installed make sure to run `sudo docker-compose pull` in `eaas-home` to pull the latest EaaS containers. 

### Updating

Do not remove the `eaasi-installer` repository from your computer, because you will be able to update to new distribution versions of EaaS: 

```sh
./scripts/update.sh ui ear docker-image
```

- `ui` — frontend
- `ear` — binary distribution of backend
- `docker-image` — runtime environment for frontend and backend

To update all components, simply run:
```sh
./scripts/update.sh
```

See [orginal notes](https://openslx.gitlab.io/eaasi-docs/install/setup.html#updating-eaasi).

### Managing the service (systemd / Linux only)

(MacOS users see below)

If you install EaaS on your laptop, you probably do not want it to start up each time you boot your system, or have it constantly running in the background, especially if you installed it on an external drive.

Disable the EaaS service so it won't automatically start:

```sh
sudo systemctl disable eaas-local
```

When the time has come, manually start it:

```sh
sudo systemctl start eaas-local
```

To gracefully stop the server, run:

```sh
sudo systemctl stop eaas-local
```

### Manual managing the EaaS server

Inside the `eaas-home` run `sudo docker-compose up` to start the service. 

**Note:** If you have a older version installed make sure to run `sudo docker-compose pull` to pull the latest EaaS containers.  


## First Steps

Access the main page at: http://localhost:8080

### Install emulators

Go to **Settings** -> **Manage Emulators** -> **Import Emulator**

To import Qemu: enter ```eaas/qemu-eaas```

To install other emulators: https://gitlab.com/emulation-as-a-service/emulators 



