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
