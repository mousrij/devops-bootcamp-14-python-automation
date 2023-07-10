## Demo Project - Website Monitoring and Recovery

### Topics of the Demo Project
Website Monitoring and Recovery

### Technologies Used
- Python
- Linode
- Docker
- Linux

### Project Description
- Create a server on a cloud platform
- Install Docker and run a Docker container on the remote server
- Write a Python script that monitors the website by accessing it and validating the HTTP response
- Write a Python script that sends an email notification when website is down
- Write a Python script that automatically restarts the application & server when the application is down

#### Steps to create a server on a cloud platform

Login to your Linode account, click on "Linodes" in the menu on the left and press "Create Linode". Select the Debian 11 image, the region Frankfurt DE (eu-central), the Shared CPU plan "Linode 2 GB", enter a root password, press "Add An SSH Key" enter a label (e.g. python-monitoring) and paste your public key (copied via `pbcopy < ~/.ssh/id_ed25519.pub`) into "SSH Public Key" field, press "Add Key" and make sure the key is checked. Press "Create Linode".

#### Steps to install Docker and run a Docker container on the remote server

When the server is running copy its IP address and execute
```sh
ssh root@<linode-ip-address>
```

Get the commands to install Docker on Debian from the [Docker docs](https://docs.docker.com/engine/install/debian/).

```sh
# Set up the repository
# ---------------------

# Update the apt package index and install packages to allow apt to use a repository over HTTPS
apt-get update
apt-get install ca-certificates curl gnupg

# Add Docker’s official GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# set up the repository
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
# ---------------------

# Update the apt package index
apt-get update

# Install Docker Engine, containerd, and Docker Compose
apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# test the installation
docker --version
```

Start an nginx container:
```sh
docker run -d -p 8080:80 nginx 
```

Open the running application in your browser: `http://<linode-ip-address>:8080`. This should open the nginx welcome page.

#### Steps to write a Python script that monitors the website

Install the Python library 'requests' needed to send HTTP requests:
```sh
pip3 install requests
```

Now create a file called `monitor-website.py` with the following content (194.233.169.74 is the linode server's ip address):

```python
import requests

try:
    response = requests.get('http://194.233.169.74:8080/')
    if response.status_code == 200:
        print('Application is running successfully!')
    else:
        print('Application Down. Fix it!')
except Exception as ex:
    print(f'Connection error happened: {ex}')
```

#### Steps to write a Python script that sends an email notification when website is down

#### Steps to write a Python script that restarts the application & server when needed
