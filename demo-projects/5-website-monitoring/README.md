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

We use our gmail account as an SMTP server to send e-mails. For the Python script to be able to authenticate with the server we need to configure the account for 2 factor authentication and add/generate an app password which we will then use in our Python script.

Login to your gmail account, click on the profile circle in the right upper corner, press "Manage your Google Account", click on "Security" in the menu on the left, scroll down to the "How you sign in to Google" section and click on the "2-Step Verification" area, turn it on and configure a second factor if it is not yet activated, scroll down to "App passwords" and click on the area, generate a password, copy the value and save it at a secure place.

Now open the `monitor-website.py` file and add content to send an e-mail as follows:

```python
import requests
import smtplib
import os

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD') # never write passwords into your python code

def send_notification(email_msg):
   print('Sending an email...')
   with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
       smtp.starttls()
       smtp.ehlo()
       smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
       message = f"Subject: SITE DOWN\n{email_msg}"
       smtp.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, message)

try:
    response = requests.get('http://194.233.169.74:8080/')
    if response.status_code == 200:
        print('Application is running successfully!')
    else:
        print('Application Down. Fix it!')
        msg = f"Application returned {response.status_code}"
        send_notification(msg)
except Exception as ex:
    print(f"Connection error happened: {ex}")
    msg = 'Application not accessible at all'
    send_notification(msg)
```

Run the script with the following commands:
```sh
export EMAIL_ADDRESS=<gmail-address>
export EMAIL_PASSWORD=<gmail-app-password>
python3 monitor-website.py
```

If you want to test the execution path when an HTTP response code other than 200 is returned, just temporarily modify the line `if response.status_code == 200:` to `if response.status_code == 300:` and run the script again.

To test the execution path when the application is not accessible at all, just temporarily modify the expression `requests.get('http://194.233.169.74:8080/')` to `requests.get('http://194.233.169.74:1234/')` and run the script again.

#### Steps to write a Python script that restarts the application & server when needed

To restart the Docker container the Python script has to ssh into the Linode server. The library [Paramiko](https://pypi.org/project/paramiko/) is a Python implementation of the SSHv2 protocol providing both client and server functionality. Before being able to use it we have to install it with the following command:

```sh
pip3 install paramiko
# ...
# Successfully installed bcrypt-4.0.1 cryptography-41.0.2 paramiko-3.2.0 pynacl-1.5.0
```

Now open the `monitor-website.py` file and add content to restart the Docker container as follows:

```python
import requests
import smtplib
import os
import paramiko  # <---
import time      # <---

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

def send_notification(email_msg):
    print('Sending an email...')
    # ...

def restart_container():  # <---
    print('Restarting the application...')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname='194.233.169.74', username='root', key_filename='/Users/fsiegrist/.ssh/id_ed25519')
   
    # get the container id of the nginx container
    stdin, stdout, stderr = ssh.exec_command("docker ps -a | grep nginx | awk '{split($0,a); print a[1]}'")
    container_id = stdout.readline()
    print(f"nginx container id = {container_id}")
   
    # stop the nginx container
    print("stopping the nginx container...")
    stdin, stdout, stderr = ssh.exec_command(f"docker stop {container_id}")
    print(stdout.readlines())

    time.sleep(2)

    # restart the nginx container
    print("starting the nginx container...")
    stdin, stdout, stderr = ssh.exec_command(f"docker start {container_id}")
    print(stdout.readlines())
    ssh.close()

try:
    response = requests.get('http://194.233.169.74:8080/')
    if response.status_code == 200:
        print('Application is running successfully!')
    else:
        print('Application Down. Fix it!')
        msg = f"Application returned {response.status_code}"
        send_notification(msg)
        restart_container()  # <---
except Exception as ex:
    print(f"Connection error happened: {ex}")
    msg = 'Application not accessible at all'
    send_notification(msg)
```

To restart the whole Linode server we need to install the library [Linode API4](https://pypi.org/project/linode-api4/) with the following command:

```sh
pip3 install linode_api4
# ...
# Successfully installed linode_api4-5.7.0 polling-0.3.2
```

To connect to a Linode server we need the Linode ID and an API token. Login to your Linode account, click on "Linodes" in the menu on the left and then on the link of the server running the nginx container. The Linode ID is displayed in the last line of the summary section at the top of the page.

To create an API token, click on your username in the top right corner of the page to open the "Profile & Account" pop up and click on the "API Tokens" link. Press the "Create A Personal Access Token" button, enter a label (e.g. python-monitoring), make sure "Read/Write" is selected for all access types and press "Create Token". Copy the personal access token and store it in a secure place. It is only displayed once!

Now open the `monitor-website.py` file and add content to restart the Linode server and the Docker container as follows:

```python
import requests
import smtplib
import os
import paramiko
import linode_api4  # <---
import time

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
LINODE_TOKEN = os.environ.get('LINODE_TOKEN')  # <---


def send_notification(email_msg):
    print('Sending an email...')
    # ...


def restart_container():
    print('Restarting the application...')
    # ...


def restart_server_and_container():  # <---
    # restart linode server
    linode_id = 47625059  # the Linode ID looked up on the Linode Management Console
    print(f"Rebooting the server with Linode ID {linode_id}...")
    client = linode_api4.LinodeClient(LINODE_TOKEN)
    nginx_server = client.load(linode_api4.Instance, linode_id)
    nginx_server.reboot()

    # restart the application
    while True:
        nginx_server = client.load(linode_api4.Instance, linode_id)
        if nginx_server.status == 'running':
            time.sleep(5)
            restart_container()
            break


try:
    response = requests.get('http://194.233.169.74:8080/')
    if response.status_code == 200:
        print('Application is running successfully!')
    else:
        print('Application Down. Fix it!')
        msg = f"Application returned {response.status_code}"
        send_notification(msg)
        restart_container()
except Exception as ex:
    print(f"Connection error happened: {ex}")
    msg = 'Application not accessible at all'
    send_notification(msg)
    restart_server_and_container()  # <---
```

Finally we want to run the monitoring process automatically on a regular basis. So we move the main code into its own function and use the scheduling feature we already know to call it every 5 minutes:

```python
import requests
import smtplib
import os
import paramiko
import linode_api4
import time
import schedule  # <---

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
LINODE_TOKEN = os.environ.get('LINODE_TOKEN')


def send_notification(email_msg):
    print('Sending an email...')
    # ...


def restart_container():
    print('Restarting the application...')
    # ...


def restart_server_and_container():
    # restart linode server
    linode_id = 47625059
    print(f"Rebooting the server with Linode ID {linode_id}...")
    # ...


def monitor_application():  # <---
    try:
        response = requests.get('http://194.233.169.74:8080/')
        if response.status_code == 200:
            print('Application is running successfully!')
        else:
            print('Application Down. Fix it!')
            msg = f"Application returned {response.status_code}"
            send_notification(msg)
            restart_container()
    except Exception as ex:
        print(f"Connection error happened: {ex}")
        msg = 'Application not accessible at all'
        send_notification(msg)
        restart_server_and_container()

schedule.every(5).minutes.do(monitor_application)  # <---

while True:  # <---
    schedule.run_pending()
    time.sleep(10)
```

This script can now be executed with the following commands:
```sh
export EMAIL_ADDRESS=<gmail-address>
export EMAIL_PASSWORD=<gmail-app-password>
export LINODE_TOKEN=<linode-access-token>
python3 monitor-website.py
```

To test the server reboot, just ssh into the Linode server and stop the nginx container.

```sh
python3 monitor-website.py
# Application is running successfully!
# Connection error happened: HTTPConnectionPool(host='194.233.169.74', port=8080): Max retries exceeded with url: / (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x1047e0810>: Failed to establish a new connection: [Errno 61] Connection refused'))
# Sending an email...
# Rebooting the server with Linode ID 47625059...
# Restarting the application...
# nginx container id = 413c31f957fd
# 
# stopping the nginx container...
# ['413c31f957fd\n']
# starting the nginx container...
# ['413c31f957fd\n']
# Application is running successfully!
```

Don't forget to delete the Linode server when you're done with the tasks.
