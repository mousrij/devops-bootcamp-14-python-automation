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