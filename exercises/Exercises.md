## Exercises for Module 14 "Automation with Python"
<br />

<details>
<summary>Exercise 1: Working with Subnets in AWS</summary>
<br />

**Tasks:**

- Get all the subnets in your default region
- Print the subnet Ids

**Solution:**

See
- [boto3](https://pypi.org/project/boto3/)
- [EC2 Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#client)
- [describe_subnets](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_subnets.html)

```python
import boto3

ec2_client = boto3.client('ec2')

subnets = ec2_client.describe_subnets(
    Filters=[
        {
            'Name': 'default-for-az',
            'Values': [
                'true',
            ]
        }
    ]
)
for subnet in subnets.get('Subnets'):
    print(subnet.get('SubnetId'))
```

</details>

******

<details>
<summary>Exercise 2: Working with IAM in AWS</summary>
<br />

**Tasks:**

- Get all the IAM users in your AWS account
- For each user, print out the name of the user and when they were last active (hint: Password Last Used attribute)
- Print out the user ID and name of the user who was active the most recently

**Solution:**

See
- [boto3](https://pypi.org/project/boto3/)
- [IAM Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#client)
- [list_users](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam/client/list_users.html)

```python
import boto3

iam_client = boto3.client('iam')

iam_users = iam_client.list_users().get('Users')
last_active_user = iam_users[0]

for iam_user in iam_users:
    print(f"{iam_user.get('UserName')} -> last active: {iam_user.get('PasswordLastUsed')}")
    if last_active_user.get('PasswordLastUsed') < iam_user.get('PasswordLastUsed'):
        last_active_user = iam_user

print("\n")
print("Last active user:")
print(f"{last_active_user.get('UserId')}: {last_active_user.get('UserName')} -> last active: {last_active_user.get('PasswordLastUsed')}")
```

</details>

******

<details>
<summary>Exercise 3: Automate Running and Monitoring Application on EC2 instance</summary>
<br />

**Tasks:**

Write Python program which automatically creates EC2 instance, install Docker inside and starts Nginx application as Docker container and starts monitoring the application as a scheduled task. Write the program with the following steps:

- Start EC2 instance in default VPC
- Wait until the EC2 server is fully initialized
- Install Docker on the EC2 server
- Start nginx container
- Open port for nginx to be accessible from browser
- Create a scheduled function that sends request to the nginx application and checks the status is OK
- If status is not OK 5 times in a row, it restarts the nginx application

**Solution:**

_Prerequisites_\
Do the following manually to prepare your AWS region for the script execution 
- open the SSH port 22 in the default security group in your default VPC 
- create key-pair for your ec2 instance. Download the private key of the key-pair and set its access permission to 400 mode
- set the values for: image_id, key_name, instance_type and ssh_privat_key_path in your python script.    

_ex3.py_
```python
import boto3
import paramiko
import requests
import schedule
import time

# eu-central-1 (= default region)
ec2_resource = boto3.resource('ec2')
ec2_client = boto3.client('ec2')

# eu-west-3
#ec2_resource = boto3.resource('ec2', region_name='eu-west-3')
#ec2_client = boto3.client('ec2', region_name='eu-west-3')

# set all needed variable values

# eu-central-1
image_id = 'ami-07ce6ac5ac8a0ee6f'
key_name = 'ec2-key-pair'
# eu-west-3
#image_id = 'ami-0f61de2873e29e866'
#key_name = 'ec2-key-pair-paris'
instance_type = 't2.small'

# the pem file must have restricted 400 permissions: 
# chmod 400 /Users/fsiegrist/.ssh/ec2-key-pair.pem
ssh_privat_key_path = '/Users/fsiegrist/.ssh/ec2-key-pair.pem' 
#ssh_privat_key_path = '/Users/fsiegrist/.ssh/ec2-key-pair-paris.pem' 
ssh_user = 'ec2-user'
ssh_host = '' # will be set dynamically below

# Start EC2 instance in default VPC

# check if we have already created this instance using instance name
response = ec2_client.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'my-server',
            ]
        },
    ]
) 

instance_already_exists = len(response.get('Reservations')) != 0 and len(response.get('Reservations')[0].get('Instances')) != 0
instance_id = ""

if not instance_already_exists: 
    print("Creating a new ec2 instance")
    ec2_creation_result = ec2_resource.create_instances(
        ImageId=image_id, 
        KeyName=key_name, 
        MinCount=1, 
        MaxCount=1, 
        InstanceType=instance_type,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': 'my-server'
                    },
                ]
            },
        ],

    )
    instance = ec2_creation_result[0]
    instance_id = instance.id
else:
    instance = response.get('Reservations')[0].get('Instances')[0]
    instance_id = instance.get('InstanceId')
    print("Instance already exists")

# Wait until the EC2 server is fully initialized
ec2_instance_fully_initialised = False

while not ec2_instance_fully_initialised:
    print("Getting instance status")
    statuses = ec2_client.describe_instance_status(
        InstanceIds = [instance_id]
    )
    if len(statuses.get('InstanceStatuses')) != 0:
        ec2_status = statuses.get('InstanceStatuses')[0]

        ins_status = ec2_status.get('InstanceStatus').get('Status')
        sys_status = ec2_status.get('SystemStatus').get('Status')
        state = ec2_status.get('InstanceState').get('Name')
        ec2_instance_fully_initialised = ins_status == 'ok' and sys_status == 'ok' and state == 'running'
    if not ec2_instance_fully_initialised:
        print("waiting for 30 seconds")
        time.sleep(30)

print("Instance fully initialised")

# get the instance's public ip address
response = ec2_client.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'my-server',
            ]
        },
    ]
) 
instance = response.get('Reservations')[0].get('Instances')[0]
ssh_host = instance.get('PublicIpAddress')

# Install Docker on the EC2 server & start nginx container

commands_to_execute = [
    'sudo yum update -y && sudo yum install -y docker',
    'sudo systemctl start docker',
    'sudo usermod -aG docker ec2-user',
    'docker run -d -p 8080:80 --name nginx nginx'
]

# connect to EC2 server
print("Connecting to the server")
print(f"public ip: {ssh_host}")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=ssh_host, username=ssh_user, key_filename=ssh_privat_key_path)

# install docker & start nginx 
for command in commands_to_execute:
    stdin, stdout, stderr = ssh.exec_command(command)
    print(stdout.readlines())

ssh.close()

# Open port 8080 on nginx server, if not already open
sg_list = ec2_client.describe_security_groups(
    GroupNames=['default']
)

port_open = False
for permission in sg_list.get('SecurityGroups')[0].get('IpPermissions'):
    print(permission)
    # some permissions don't have FromPort set
    if 'FromPort' in permission and permission.get('FromPort') == 8080:
        port_open = True

if not port_open:
    sg_response = ec2_client.authorize_security_group_ingress(
        FromPort=8080,
        ToPort=8080,
        GroupName='default',
        CidrIp='0.0.0.0/0',
        IpProtocol='tcp'
    )

# Scheduled function to check nginx application status and reload if not OK 5x in a row
app_not_accessible_count = 0

def restart_container():
    print('Restarting the application...')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=ssh_host, username=ssh_user, key_filename=ssh_privat_key_path)
    stdin, stdout, stderr = ssh.exec_command('docker start nginx')
    print(stdout.readlines())
    ssh.close()
    # reset the count
    global app_not_accessible_count
    app_not_accessible_count = 0
    
    print(app_not_accessible_count)


def monitor_application():
    global app_not_accessible_count
    try:
        response = requests.get(f"http://{ssh_host}:8080")
        if response.status_code == 200:
            print('Application is running successfully!')
        else:
            print('Application Down. Fix it!')
            app_not_accessible_count += 1
            if app_not_accessible_count == 5:
                restart_container()
    except Exception as ex:
        print(f'Connection error happened: {ex}')
        print('Application not accessible at all')
        app_not_accessible_count += 1
        if app_not_accessible_count == 5:
            restart_container()
        return "test"
    
schedule.every(10).seconds.do(monitor_application)  

while True:
    schedule.run_pending()
    time.sleep(1)
```

</details>

******

<details>
<summary>Exercise 4: Working with ECR in AWS</summary>
<br />

**Tasks:**

- Get all the repositories in ECR
- Print the name of each repository
- Choose one specific repository and for that repository, list all the image tags inside, sorted by date, here the most recent image tag is on top.

**Solution:**

See
- [ECR Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecr.html#client)
- [describe_repositories](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecr/client/describe_repositories.html)
- [describe_images] (https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecr/client/describe_images.html)

If there is no ECR repository available in your region, do exercise 5 first.

```python
import boto3

ecr_client = boto3.client('ecr')

# Get all ECR repos and print their names
repos = ecr_client.describe_repositories().get('repositories')
for repo in repos:
    print(repo.get('repositoryName'))

print("-----------------------")

# For one specific repo, get all the images and print them out sorted by date
repo_name = "java-app" # replace with your own repo-name
images = ecr_client.describe_images(
    repositoryName=repo_name
)

image_tags = []

for image in images.get('imageDetails'):
    image_tags.append({
        'tag': image.get('imageTags'),
        'pushed_at': image.get('imagePushedAt')
    })

images_sorted = sorted(image_tags, key=lambda tag: tag.get('pushed_at'), reverse=True)
for image in images_sorted:
    print(image)
```

Run the script:
```sh
python3 ex4.py
# java-maven-app
# -----------------------
# {'tag': ['3.0'], 'pushed_at': datetime.datetime(2023, 7, 21, 16, 55, 20, tzinfo=tzlocal())}
# {'tag': ['2.0'], 'pushed_at': datetime.datetime(2023, 7, 21, 16, 54, 20, tzinfo=tzlocal())}
# {'tag': ['1.0'], 'pushed_at': datetime.datetime(2023, 7, 21, 16, 51, 11, tzinfo=tzlocal())}
```

</details>

******

<details>
<summary>Exercise 5: Python in Jenkins Pipeline</summary>
<br />

**Tasks:**

Create a Jenkins job that fetches all the available images from your application's ECR repository using Python. It allows the user to select the image from the list through user input and deploys the selected image to the EC2 server using Python.

Do the following preparation manually:

- Start EC2 instance and install Docker on it
- Install Python, Pip and all needed Python dependencies in Jenkins
- Create 3 Docker images with tags 1.0, 2.0, 3.0 from one of the previous projects

Once all the above is configured, create a Jenkins Pipeline with the following steps:

- Fetch all 3 images from the ECR repository (using Python)
- Let the user select the image from the list ([hint](https://www.jenkins.io/doc/pipeline/steps/pipeline-input-step/))
- SSH into the EC2 server (using Python)
- Run docker login to authenticate with ECR repository (using Python)
- Start the container from the selected image from step 2 on EC2 instance (using Python)
- Validate that the application was successfully started and is accessible by sending a request to the application (using Python)

**Solution:**

Login to your AWS Management Console account and navigate to the EC2 starting page. Create a new EC2 instance. Add a inbound rule to the security group opening the port 22 for ssh from 'my-ip' (the IP address of your local machine). SSH into the EC2 instance as 'ec2-user' and install Docker using the following commands:
```sh
ssh -i ~/.ssh/ec2-key-pair.pem ec2-user@<ec2-instance-ip>

sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user
```

SSH as root into your Jenkins-Droplet and install Python using the following commands:
```sh
ssh root@<jenkins-droplet-ip>
docker exec -u 0 -it <jenkins-container-id> /bin/bash

apt-get update
apt-get install python3
apt-get install pip
pip install boto3
pip install paramiko
pip install requests
```

Login to your AWS Management Console account and navigate to the Elastic Container Registry starting page. Create a new private repository named 'java-maven-app'.

Check out the java-maven-app from [GitHub](https://github.com/fsiegrist/devops-bootcamp-java-maven-app). Execute the following commands to build the application, create three Docker image tags and push the to the ECR:
```sh
cd <java-maven-app/project/root/directory>
# step 1: build application
mvn clean package
# step 2: build docker image
docker build -t java-maven-app .
# step 3: create image tag
docker tag java-maven-app:latest 369076538622.dkr.ecr.eu-central-1.amazonaws.com/java-maven-app:1.0

# increase the version in the pom.xml and repeat steps 1 to 3 (increasing the tag version in step 3 to 2.0); then do it a third time for tag 3.0

# authenticate the docker client to the ECR
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 369076538622.dkr.ecr.eu-central-1.amazonaws.com
# push the 3 image tags to the repository
docker push 369076538622.dkr.ecr.eu-central-1.amazonaws.com/java-maven-app:1.0
docker push 369076538622.dkr.ecr.eu-central-1.amazonaws.com/java-maven-app:2.0
docker push 369076538622.dkr.ecr.eu-central-1.amazonaws.com/java-maven-app:3.0
```

Login as admin user to your Jenkins Management Console, go to the dashboard and open the 'devops-bootcamp-multibranch-pipeline' pipeline. Open the pipeline specific credentials and make sure there are still 'Secret Text' credentials with IDs 'jenkins-aws_access_key_id' and 'jenkins-aws_access_key_id' and 'SSH Username with private key' crendentials with ID 'ec2-server-key'. If not create them. Finally create new credentials of type 'Secret Text' named 'ecr-repo-pwd' and store the ECR password you copy with the following command:
```sh
aws ecr get-login-password --region eu-central-1 | pbcopy
```

Go to the root directory of the java-maven-app project and create a new branch named 'feature/python'. Create a directory called 'python' and add the following files:

_python/get-images.py_
```python
import boto3
import os

repo_name = os.environ.get('ECR_REPO_NAME')

ecr_client = boto3.client('ecr')

# Fetch all 3 images from ECR repo
images = ecr_client.describe_images(repositoryName=repo_name)

image_tags = []
for image in images.get('imageDetails'):
    image_tags.append(image.get('imageTags')[0])

for tag in image_tags:
    print(tag)
```

_python/deploy.py_
```python
import os
import paramiko

# get all the env vars set in Jenkinsfile
ssh_host = os.environ.get('EC2_SERVER')
ssh_user = os.environ.get('EC2_USER')
ssh_private_key = os.environ.get('SSH_KEY_FILE')

docker_registry = os.environ.get('ECR_REGISTRY')
docker_user = os.environ.get('DOCKER_USER')
docker_pwd = os.environ.get('DOCKER_PWD')
docker_image = os.environ.get('DOCKER_IMAGE') # version is selected by user in Jenkins 
container_port = os.environ.get('CONTAINER_PORT')
host_port = os.environ.get('HOST_PORT')

# SSH into the EC2 server
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=ssh_host, username=ssh_user, key_filename=ssh_private_key)

stdin, stdout, stderr = ssh.exec_command(f"echo {docker_pwd} | docker login {docker_registry} --username {docker_user} --password-stdin")
print(stdout.readlines())
stdin, stdout, stderr = ssh.exec_command(f"docker run -p {host_port}:{container_port} -d {docker_image}")
print(stdout.readlines())

ssh.close()
```

_python/validate.py_
```python
from wsgiref.util import request_uri
import requests
import time
import os

ssh_host = os.environ.get('EC2_SERVER')
host_port = os.environ.get('HOST_PORT')

# Validate the application started successfully
try:
    # give the app some time to start up
    time.sleep(15)
    
    response = requests.get(f"http://{ssh_host}:{host_port}")
    if response.status_code == 200:
        print('Application is running successfully!')
    else:
        print('Application deployment was not successful')
except Exception as ex:
    print(f'Connection error happened: {ex}')
    print('Application not accessible at all')
```

Replace the content of the Jenkinsfile with the following:

```groovy
#!/usr/bin/env groovy

pipeline {
    agent any
    environment {
        ECR_REPO_NAME = 'java-maven-app' // SET VALUE
        EC2_SERVER = '18.185.89.127' // SET VALUE
        EC2_USER = 'ec2-user'
        
        // will be set to the location of the SSH key file that is temporarily created
        SSH_KEY_FILE = credentials('ec2-server-key')

        ECR_REGISTRY = '369076538622.dkr.ecr.eu-central-1.amazonaws.com' // SET VALUE
        DOCKER_USER = 'AWS'
        DOCKER_PWD = credentials('ecr-repo-pwd')
        CONTAINER_PORT = '8080' // SET VALUE
        HOST_PORT = '8080' // SET VALUE

        AWS_ACCESS_KEY_ID = credentials('jenkins-aws_access_key_id')
        AWS_SECRET_ACCESS_KEY = credentials('jenkins-aws_secret_access_key')
        AWS_DEFAULT_REGION = 'eu-central-1' // SET VALUE
    }
    stages {
        stage('select image version') {
            steps {
                script {
                    echo 'fetching available image versions'
                    def result = sh(script: 'python3 python/get-images.py', returnStdout: true).trim()
                    // split returns an Array, but choices expects either List or String, so we do "as List"
                    def tags = result.split('\n') as List
                    version_to_deploy = input message: 'Select version to deploy', ok: 'Deploy', parameters: [choice(name: 'Select version', choices: tags)]
                    // put together the full image name
                    env.DOCKER_IMAGE = "${ECR_REGISTRY}/${ECR_REPO_NAME}:${version_to_deploy}"
                    echo env.DOCKER_IMAGE
                }
            }
        }
        stage('deploying image') {
            steps {
                script {
                    echo 'deploying docker image to EC2...'
                    def result = sh(script: 'python3 python/deploy.py', returnStdout: true).trim()
                    echo result
                }
            }
        }
        stage('validate deployment') {
            steps {
                script {
                    echo 'validating that the application was deployed successfully...'
                    def result = sh(script: 'python3 python/validate.py', returnStdout: true).trim()
                    echo result
                }
            }
        }
    }
}
```

Commit and push the new branch. The multi-pipeline build should detect the new branch and start building it automatically. Note that during the 'select image version' stage, the build is waiting for user input.

Don't forget to cleanup all the AWS resources when you've finished the exercise.

</details>

******