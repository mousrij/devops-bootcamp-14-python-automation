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
