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
