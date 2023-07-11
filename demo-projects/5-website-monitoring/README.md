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
        msg = f'Application returned {response.status_code}'
        send_notification(msg)
except Exception as ex:
    print(f'Connection error happened: {ex}')
    msg = 'Application not accessible at all'
    send_notification(msg)
```

Run the script with the following command:
```sh
export EMAIL_ADDRESS=felix.siegrist@gmail.com; export EMAIL_PASSWORD=<app-password>; python3 monitor-website.py
```

If you want to test the execution path when an HTTP response code other than 200 is returned, just temporarily modify the line `if response.status_code == 200:` to `if response.status_code == 300:` and run the script again.

To test the execution path when the application is not accessible at all, just temporarily modify the expression `requests.get('http://194.233.169.74:8080/')` to `requests.get('http://194.233.169.74:1234/')` and run the script again.

#### Steps to write a Python script that restarts the application & server when needed

