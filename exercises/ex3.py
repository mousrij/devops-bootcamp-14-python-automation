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
