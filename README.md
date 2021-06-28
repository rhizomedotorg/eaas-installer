# EaaS Local-Mode Installation

This installer is able to deploy EaaS on a local computer (localhost) for testing / experiments.  This documentation is based on the EaaS-CI test runner (https://gitlab.com/emulation-as-a-service/experiments/eaas-ci-test).  

- This will work on Linux and Mac OSX. Other OS might work, but untested.
- By default EaaS will be installed as a systemd service and requires Docker to be installed as a systemd service as well.
- The EaaS interface will be accessible at `http://localhost:8080`.

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

Finally, install python dependencies via Python PIP:
   ```bash
   sudo pip3 install docker-compose ansible jmespath
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
      eaas_home: "/eaas-home-local"  ## on a drive with lots of space!
      eaas_service_name: "eaas-local" ## on systemd capable systems (e.g. ubuntu) a service unit will be created

    docker:
      image: "eaas/eaas-appserver"
      port: 8080	# Don't change the port.

    ui:
      enable_network_sessions: true
      enable_containers: true
      enable_webrtc: true
      standalone: true
    
    eaas:
      enable_oaipmh_provider: true
      db_upgrade: true

    operator:
      release:
        channel: "eaas"
        version: "210625.0"
      channels:
      - location: "https://gitlab.com/api/v4/projects/emulation-as-a-service%2feaas-releases/jobs/artifacts/master/raw/public/channels/eaas.json?job=pages"


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



