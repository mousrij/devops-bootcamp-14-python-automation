## Demo Project - Automate configuring EC2 Server Instances

### Topics of the Demo Project
Automate configuring EC2 Server Instances

### Technologies Used
- Python
- Boto3
- AWS

### Project Description
- Write a Python script that automates adding environment tags to all EC2 server instances

#### Steps to write a Python script that automates adding environment tags to all EC2 server instances

Go to the [EC2 Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#client) documentation and look for the [describe_instances](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_instances.html) function.

Then got to the [EC2 ServiceResource](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/service-resource/index.html) documentation and look for the [create_tags](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/service-resource/create_tags.html) function.

Create an `add-env-tags.py` file with the following content:

```python
import boto3

def add_tags_to_ec2_instances_in_region(region, tags):
    ec2_client = boto3.client('ec2', region_name=region)
    instance_ids = []
    reservations = ec2_client.describe_instances()['Reservations']
    for res in reservations:
        instances = res['Instances']
        for ins in instances:
            instance_ids.append(ins['InstanceId'])

    ec2_resource = boto3.resource('ec2', region_name=region)
    response = ec2_resource.create_tags( # the same function also exists on ec2_client
        Resources=instance_ids,
        Tags=tags
    )

add_tags_to_ec2_instances_in_region('eu-west-3', [{'Key': 'environment', 'Value': 'prod'}])
add_tags_to_ec2_instances_in_region('eu-central-1', [{'Key': 'environment', 'Value': 'dev'}])
```

Open the AWS Management Webconsole and create two EC2 instances in the region 'eu-west-3' (Paris) and one in 'eu-central-1' (Frankfurt). When they are up and running, execute the Python script `python3 add-env-tags.py` and check the tags of the instances in Paris and Frankfurt. The two instances in Paris should have the tag `environment=prod` and the instance in Frnakfurt should have `environment=dev`.

Don't forget to terminate all three instances when you're done.
