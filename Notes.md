## Notes on the videos for Module 14 "Automation with Python"
<br />

<details>
<summary>Video: 1 - Introduction to Boto Library (AWS SDK for Python)</summary>
<br />

Automating repetitive maintenance tasks like
- doing regular back-ups
- doing regular clean-ups 
- configuration on existing servers 
- doing health-checks/monitoring

can be best achieved using a programming language like Python.

Boto3 is a Python library providing an AWS SDK to create, configure and manage AWS services like EC2, S3, etc. If you need to communicate with Azure or Google Cloud, there are different libraries available specific to those cloud platforms.

</details>

*****

<details>
<summary>Video: 2 - Install Boto3 and connect to AWS</summary>
<br />

To install Boto3, execute
```sh
pip3 install boto3
# ...
# Successfully installed boto3-1.26.165 botocore-1.29.165 jmespath-1.0.1 python-dateutil-2.8.2 s3transfer-0.6.1 urllib3-1.26.16
```

Now you can import Boto3 into your Python scripts and use it:
```python
import boto3
```

To connect to AWS and authenticate against your AWS account using Boto3, nothing special has to be done. Boto3 will use the configuration in the `~/.aws/config` and `~/.aws/credentials` files.

</details>

*****

<details>
<summary>Video: 3 - Getting familiar with Boto</summary>
<br />
<img src="./images/image.png" />
To find a detailed documentation of the Boto3 library, check out the [Boto3 documentation page](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html).
However, it is not very easy to find the documentation for the tasks you want to program. For example if we want to list all VPCs available in our region, we have to know that VPCs are related to EC2, so we click on the link for [EC2](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html), and 
then find the documentation for [describe_vpcs](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_vpcs.html), where you get information about required and optional parameters as well as about the structure of the response.

```python
import boto3

# list all available VPCs in my region
ec2_client = boto3.client('ec2')
all_available_vpcs = ec2_client.describe_vpcs()
vpcs = all_available_vpcs.get('Vpcs')
for vpc in vpcs:
    print(vpc.get('VpcId'))
    cidr_block_association_sets = vpc.get('CidrBlockAssociationSet')
    for cidr_block_association_set in cidr_block_association_sets:
        cidr_block_association_set.get('CidrBlockState').get('State')

# do the same for a region other than the default region
ec2_client = boto3.client('ec2', region_name='eu-west-3')
# ...
```

### Create VPC and Subnet
Go back to the [EC2](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html) documentation and search for the documentation of [create_vpc](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/create_vpc.html).

```python
import boto3

# create a VPC
ec2_client = boto3.client('ec2')
vpc_resp = ec2_client.create_vpc(
    CidrBlock='10.0.0.0/16'
)
vpc_id = vpc_resp.get('Vpc').get('VpcId')

# create a subnet in the new VPC
# using the ec2 client
ec2_client.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.1.0/24'
)

# or using the VPC resource (resources are an object oriented abstraction using clients under the hood)
ec2_resource = boto3.resource('ec2', resource_name='...')
vpc = ec2_resource.Vpc(vpc_id)
vpc.create_subnet(
    CidrBlock='10.0.2.0/24'
)

# add a name tag to the new VPC
# using the ec2 client
ec2_client.create_tags(
    Resources=[
        vpc_id,
    ],
    Tags=[
        {
            'Key': 'Name',
            'Value': 'my-vpc',
        },
    ],
)

# or using the VPC resource
vpc.create_tags(
    Tags=[
        {
            'Key': 'Name',
            'Value': 'my-vpc',
        },
    ],
)
```

</details>

*****

<details>
<summary>Video: 4 - Terraform vs Python - understand when to use which tool</summary>
<br />

As we saw, Python can also be used for infrastructure provisioning, but Terraform is much better for this use case.

Terraform
- manages state of the infrastructure, so it knows the current state
- knows the difference of current and your configured/desired state
- is idempotent (multiple execution of same config file, will aways result in same end result)
- lets you declare the desired end result

Whereas Python
- doesn't have a state
- is not idempotent
- makes you explicitly write what you want to do (imperative style)
- is more low level, so it's more flexible and you can write very complex logic (like monitoring, creating backups, do scheduled tasks, add a web interface to all this functionality, etc.)

</details>

*****

<details>
<summary>Video: 5 - Health Check: EC2 Status Checks</summary>
<br />

Imagine you have provisioned hundreds of EC2 instances using Terraform. You also configured autoscaling, so there are always instances being initialized, running, shutting down or terminated. We want to have an overview of the current state of all these instances and write a Python script that periodically checks the state of all instances.

See [demo project #1](./demo-projects/1-ec2-status-check/)

</details>

*****

<details>
<summary>Video: 6 - Write a Scheduled Task in Python</summary>
<br />

To implement scheduled tasks, install the [schedule](https://pypi.org/project/schedule/) library:

```sh
pip3 install schedule
```

It allows to schedule tasks in a comfortable way:

```python
import schedule
import time

def job():
    print("I'm working...")

schedule.every(10).seconds.do(job)
schedule.every(10).minutes.do(job)
schedule.every().hour.do(job)
schedule.every().day.at("10:30").do(job)
schedule.every(5).to(10).minutes.do(job)
schedule.every().monday.do(job)
schedule.every().wednesday.at("13:15").do(job)
schedule.every().day.at("12:42", "Europe/Paris").do(job)  # needs the pytz package to be installed
schedule.every().minute.at(":17").do(job)

def job_with_argument(name):
    print(f"I am {name}")

schedule.every(10).seconds.do(job_with_argument, name="Peter")

while True:
    schedule.run_pending()
    time.sleep(1)
```

We can use it to schedule our status check task in [demo project #1](./demo-projects/1-ec2-status-check/):

```python
schedule.every(5).seconds.do(check_instance_status)
```

Run the script and terminate two instances by deleting their configuration blocks in the terraform configuration file and re-applying the terraform file. You should see the changing status information in the output of the Python script.

</details>

*****

<details>
<summary>Video: 7 - Configure Server: Add Environment Tags to EC2 Instances</summary>
<br />

Imagine you have provisioned lots of EC2 instances in the Paris region and others in the Frankfurt region. Now you want to add a 'production' tag to all the instances in the Paris region and a 'development' tag to all of those in the Frankfurt region. You don't want to do that manually on each instance but rather write a Python script that does it automatically for all the instances.

See [demo project #2](./demo-projects/2-ec2-configuration/)

</details>

*****

<details>
<summary>Video: 8 - EKS cluster information</summary>
<br />

Imagine you have provisioned 10 EKS cluster and want to know for each of these the cluster status, which Kubernetes version is running on the cluster and what is the cluster endpoint.

See [demo project #3](./demo-projects/3-eks-cluster-info/)

</details>

*****

<details>
<summary>Video: 9 - Backup EC2 Volumes: Automate creating Snapshots</summary>
<br />

Imagine you have provisioned lots of EC2 instances and want to automate the task of creating backups of their volumes (volume snapshots) on a daily bases.

See [demo project #4](./demo-projects/4-backup-and-restore/)

</details>

*****

<details>
<summary>Video: 10 - Automate cleanup of old Snapshots</summary>
<br />

Creating a backup of each EC2 instance volume every day will result in a lot of backups after a while. So you decide to write a Python script that automates the task of deleting all the snapshots except for the two most recent ones of each volume. This script may be used to cleanup the backups from time to time.

See [demo project #4](./demo-projects/4-backup-and-restore/)

</details>

*****

<details>
<summary>Video: 11 - Automate restoring EC2 Volume from the Backup</summary>
<br />

Imagine an EC2 instance has problems because its volume got corrupted. For such cases we want to have a Python script that automatically creates a new volume from the latest snapshot of the corrupted volume (assuming that this snapshot was still ok) and attach the new volume to the EC2 instance.

See [demo project #4](./demo-projects/4-backup-and-restore/)

</details>

*****

<details>
<summary>Video: 12 - Handling Errors</summary>
<br />

It's important to handle possible errors in your Python programs properly. If errors are not handled properly, it can lead to data loss, corrupt data etc. It is generally a good practice to completely roll back and clean up half-created resources. In Python we have to care about this ourselves because we don't have a state as we do when using Terraform.

</details>

*****

<details>
<summary>Video: 13 - Website Monitoring 1: Scheduled Task to Monitor Application Health</summary>
<br />

Now we are going to monitor a simple website (nginx) which is running in a Docker container on a Linode cloud server. The monitoring is done using a Python script that checks the accessibility of an endpoint provided by the nginx container. 

See [demo project #5](./demo-projects/5-website-monitoring/)

</details>

*****

<details>
<summary>Video: 14 - Website Monitoring 2: Automated Email Notification</summary>
<br />

If the nginx endpoint is not successfully accessible, we want our Python script to send us a notification via e-mail.

See [demo project #5](./demo-projects/5-website-monitoring/)

</details>

*****

<details>
<summary>Video: 15 - Website Monitoring 3: Restart Application and Reboot Server</summary>
<br />

If the nginx endpoint is not successfully accessible, we want our Python script to try to fix the problem automatically. It should first try to restart the Docker container. If this is not possible because the whole cloud server is down, it should try to restart the Linode server.

See [demo project #5](./demo-projects/5-website-monitoring/)

</details>

*****