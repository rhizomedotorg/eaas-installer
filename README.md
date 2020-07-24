# EaaS laptop install

This guide is based on the original [Setup and Deployment guide](https://openslx.gitlab.io/eaasi-docs/install/setup.html) and the [EaaSI installer README](https://gitlab.com/eaasi/eaasi-installer/-/blob/master/README.md).

Goal of the process described here is to install EaaS on a local computer using an automated installer from the EaaSI project, in most cases to prepare environments to be published on Rhizome's public infrastructure.

- This will only work on Linux, the description here is for Ubuntu version 18.04 or above.
- EaaS will be installed as a systemd service and requires Docker to be installed as a systemd service as well.
- The EaaS interface will be accessible at `http://localhost:8080`.

## Preconditions

1. **Optional:** To access certain branches you need a GitLab account and generate a personal access token. You can safely skip this point if unsure.
   1. Go the [Personal Access Token](https://gitlab.com/profile/personal_access_tokens) settings page.
   2. Pick a random name and check all checkboxes: api, read_repository
   3. Create the token and note the displated string (it is not possible to display it again.
   4. Ask the EaaS team to integrate your GitLab account user name in their team. `klaus.rechert@rz.uni-freiburg.de`. Let them know your GitLab user name.
2. All repositories need to be set up so that when running `sudo apt update` no errors are generated. For instance, repositories with expired certificates, invalid or missing GPG keys, or one that are just offline at the moment, need to be removed from the active repository list. Identify possible offenders by running `sudo apt update` and deactive them with Ubuntu's **Software & Updates** app.
3. [Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/) needs to be installed and working. 
4. [docker-compose](https://docs.docker.com/compose/) It is recommended to install the latest version of `docker-compose`.
5.
   a. **Method 1:** Install static binary (recommended): 
       
      ```bash
      sudo curl -L "https://github.com/docker/compose/releases/download/1.25.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
      ```
       
    b. **Method 2**  via python instead of using the version from Docker's repo:
   ```bash
   sudo pip3 install docker-compose
   ```
   
4. Ansible needs to be installed. [Follow the instructions](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#latest-releases-via-apt-ubuntu) or hope for the best when using these commands:
   ```bash
   sudo pip3 install ansible
   ```


## Base Installation and Setup

The installation process is based on an Ansible *playbook*, a set of scripts that make changes to the computer's configuration based on parameters in a bunch of yaml files. Some of these parameters need to be tweaked depending on local requirements.

The installation process is supposed to run only once. To update the setup with new versions of EaaS, a separate updater is used.

1. Clone the repository `eaasi-installer` and change into the repo's diretory:
   ```bash
   git clone git@gitlab.com:eaasi/eaasi-installer.git
   cd eaasi-installer
   ```

2. Run the preparation script and specify that you want to install locally:
	 ```bash
   ./scripts/prepare.sh --local-mode
   ```

3. Copy template setup files to the place where the installer expects them. For the local computer use-case, it should be these ones:
   ```bash
   cp ./config/localhost.yaml.template ./artifacts/config/hosts.yaml
   cp ./config/eaasi.yaml.template ./artifacts/config/eaasi.yaml
   ```

4. Make changes to `artifacts/hosts.yaml`
     ```yaml
     ---
     all:
       hosts:
         eaas-gateway:
           ansible_user: despens  ## change to your local username.
           ansible_host: localhost
           ansible_connection: local
     ```

**Note:** `ansible_user` requires sudo capabilities. 

5. Make changes to `artifacts/eaasi.yaml`:
    ```yaml
    ---
    host:
      build_dir: "/eaas-build" ## Set up target directories
      eaas_home: "/eaas-home"  ## on a drive with lots of space!

    docker:
      image: "eaas/eaas-appserver"
      port: 8080	# Don't change the port.

      ## For a locahost connection, SSL is not required,
      ## Keep commented out.
      
      # to enable SSL with custom certificate,
      # uncomment the following lines...
      #port: 443
      #ssl:
      #  enabled: true
      #  certificate: "./artifacts/ssl/server.crt"
      #  private_key: "./artifacts/ssl/server.key"

    ui:
      git_branch: "master"
      
      ## Comment out http_auth unless you want to type in
      ## an extra password into your browser.
      
      # http_auth:
      #   user: "eaasi"
      #   password: "demo"

    eaas:
      git_branch: "master"
      enable_oaipmh_provider: true
      db_upgrade: true

    ## eaas_private_token: "abc123" ## Your GitLab personal access token string
    eaas_project_id: "10009002" ## project id public 'emulation-as-a-service'  
    ## ui_private_token: "abc123" ## Your GitLab personal access token string
    ui_project_id: "10009004" ## project id public 'emulation-as-a-service
    ```
6. Run `./scripts/deploy.sh` — after a few minutes, you should have your very own EaaS node running on your computer.

## Maintenance

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

### Managing the service

If you install EaaS on your laptop, you probably do not want it to start up each time you boot your system, or have it constantly running in the background, especially if you installed it on an external drive.

Disable the EaaS service so it won't automatically start:

```sh
sudo systemctl disable eaas
```

When the time has come, manually start it:

```sh
sudo systemctl start eaas
```

To gracefully stop the server, run:

```sh
sudo systemctl stop eaas
```

## First Steps

Access the main page at: http://localhost:8080

### Install emulators

Go to **Settings** -> **Manage Emulators** -> **Import Emulator**

To import Qemu: enter ```eaas/qemu-eaas```

To install other emulators: https://gitlab.com/emulation-as-a-service/emulators 



