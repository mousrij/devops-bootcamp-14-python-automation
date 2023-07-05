## Demo Project - EC2 Status Checks

### Topics of the Demo Project
Health Check: EC2 Status Checks

### Technologies Used
- Python
- Boto3
- AWS
- Terraform

### Project Description
- Create EC2 Instances with Terraform
- Write a Python script that fetches statuses of EC2 instances and prints to the console
- Extend the Python script to continuously check the status of EC2 instances in a specific interval


#### Steps to create EC2 instances with Terraform

Get the `terraform` folder of module 12, demo project 1 and copy the `resource "aws_instance" "myapp-server"` block in the `main.tf` configuration file to have it three times (`"myapp-server-one"`, `"myapp-server-two"` and `"myapp-server-three"`).

Create the instances executing the following commands:

```sh
cd terraform

terraform init
# ...
# Terraform has been successfully initialized!

terraform apply --auto-approve
# ...
# Apply complete! Resources: 9 added, 0 changed, 0 destroyed.

# Outputs:

# ec2_public_ip_one = "52.57.137.123"
# ec2_public_ip_three = "18.185.29.122"
# ec2_public_ip_two = "3.70.120.2"
```

#### Steps to write a Python script that fetches statuses of EC2 instances

Go to the [EC2 Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#client) documentation and look for the [describe_instance_status](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_instance_status.html) function. 

Create an `ec2-status-check.py` file with the following content:

```python
import boto3

ec2_client = boto3.client('ec2', region_name="eu-central-1")

statuses = ec2_client.describe_instance_status(
    IncludeAllInstances=True # needed to get the status of all instances, not just the running ones
)
for status in statuses.get('InstanceStatuses'):
    ins_status = status.get('InstanceStatus').get('Status')
    sys_status = status.get('SystemStatus').get('Status')
    state = status.get('InstanceState').get('Name')
    print(f"Instance {status.get('InstanceId')} is {state} with instance status {ins_status} and system status {sys_status}")

print("==================\n")
```

#### Steps to extend the Python script to continuously check the status of EC2 instances

Install the `schedule` library:
```sh
pip3 install schedule
# Collecting schedule
#   Downloading schedule-1.2.0-py2.py3-none-any.whl (11 kB)
# Installing collected packages: schedule
# Successfully installed schedule-1.2.0
```

And use it in the script to run the status check every 5 seconds. Adjust the script as follows (`# <---` indicates the necessary changes): 
```python
import boto3
import schedule # <---
import time     # <---

ec2_client = boto3.client('ec2', region_name="eu-central-1")


def check_instance_status(): # <---
    statuses = ec2_client.describe_instance_status(
        IncludeAllInstances=True
    )
    for status in statuses.get('InstanceStatuses'):
        ins_status = status.get('InstanceStatus').get('Status')
        sys_status = status.get('SystemStatus').get('Status')
        state = status.get('InstanceState').get('Name')
        print(f"Instance {status.get('InstanceId')} is {state} with instance status {ins_status} and system status {sys_status}")

    print("==================\n")


schedule.every(5).seconds.do(check_instance_status) # <---

while True:                # <---
    schedule.run_pending() # <---
    time.sleep(1)          # <---
```

Run the script while adding or deleting EC2 instances (using the terraform configuration file) to see the status changes in the output of the script.

```
$> terraform apply

Instance i-0c875de034ec0f645 is pending with instance status not-applicable and system status not-applicable
Instance i-0f4642a554d17af0d is pending with instance status not-applicable and system status not-applicable
Instance i-05043f8da49532e64 is pending with instance status not-applicable and system status not-applicable
==================

Instance i-0c875de034ec0f645 is running with instance status initializing and system status initializing
Instance i-0f4642a554d17af0d is running with instance status initializing and system status initializing
Instance i-05043f8da49532e64 is running with instance status initializing and system status initializing
==================

Instance i-0c875de034ec0f645 is running with instance status ok and system status ok
Instance i-0f4642a554d17af0d is running with instance status initializing and system status initializing
Instance i-05043f8da49532e64 is running with instance status ok and system status ok
==================

Instance i-0c875de034ec0f645 is running with instance status ok and system status ok
Instance i-0f4642a554d17af0d is running with instance status ok and system status ok
Instance i-05043f8da49532e64 is running with instance status ok and system status ok
==================

$> terraform destroy

Instance i-0c875de034ec0f645 is shutting-down with instance status not-applicable and system status not-applicable
Instance i-0f4642a554d17af0d is shutting-down with instance status not-applicable and system status not-applicable
Instance i-05043f8da49532e64 is shutting-down with instance status not-applicable and system status not-applicable
==================

Instance i-0c875de034ec0f645 is terminated with instance status not-applicable and system status not-applicable
Instance i-0f4642a554d17af0d is terminated with instance status not-applicable and system status not-applicable
Instance i-05043f8da49532e64 is terminated with instance status not-applicable and system status not-applicable
==================
```
