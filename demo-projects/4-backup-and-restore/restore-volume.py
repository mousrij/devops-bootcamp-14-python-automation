import boto3
import time

ec2_client = boto3.client('ec2', region_name="eu-central-1")

# the id of the EC2 instance with the corrupted volume
instance_id = "i-08e1b0f41182fc0e9"

volumes = ec2_client.describe_volumes(
    Filters=[
        {
            'Name': 'attachment.instance-id',
            'Values': [instance_id]
        }
    ]
)

instance_volume = volumes.get('Volumes')[0]

snapshots = ec2_client.describe_snapshots(
    OwnerIds=['self'],
    Filters=[
        {
            'Name': 'volume-id',
            'Values': [instance_volume.get('VolumeId')]
        }
    ]
)

latest_snapshot = sorted(snapshots['Snapshots'], key=lambda snap: snap.get('StartTime'), reverse=True)[0]
print(latest_snapshot.get('StartTime'))

new_volume = ec2_client.create_volume(
    SnapshotId=latest_snapshot.get('SnapshotId'),
    AvailabilityZone="eu-central-1a",
    TagSpecifications=[
        {
            'ResourceType': 'volume',
            'Tags': [
                {
                    'Key': 'Environment',
                    'Value': 'Production'
                }
            ]
        }
    ]
)

new_volume_id = new_volume.get('VolumeId')

ec2_resource = boto3.resource('ec2', region_name="eu-central-1")

# wait until the new volume is available before attaching it to the EC2 instance
while True:
    new_vol = ec2_resource.Volume(new_volume_id)
    print(new_vol.state)
    if new_vol.state == 'available':
        ec2_resource.Instance(instance_id).attach_volume(
            VolumeId=new_volume_id,
            Device='/dev/xvdb'
        )
        break
    time.sleep(1)
