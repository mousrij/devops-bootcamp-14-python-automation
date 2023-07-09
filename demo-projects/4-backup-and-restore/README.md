## Demo Project - Data Backup & Restore

### Topics of the Demo Project
Data Backup & Restore

### Technologies Used
- Python
- Boto3
- AWS

### Project Description
- Preparation: Create two EC2 instances
- Write a Python script that automates creating backups for production EC2 volumes
- Write a Python script that cleans up old EC2 volume snapshots
- Write a Python script that restores EC2 volumes

#### Steps to create two EC2 instances

Log in to your AWS Management Console in the browser and navigate to the EC2 dashboard. Press the "Launch instance" button. Leave the defaults (Amazon Linux 2023 AMI, t2.micro, default security group, default subnet or create a new one, no key pair, 8 GiB gp3 volume) and increase the number of instances to be created to 2. Press the "Launch instance" button.

Go to the instance overview and click into the "Name" field to edit the name tags. Set "dev" for the first instance and "prod" for the second one. Click on the dev instance, open the "Storage" tab, click on the volume ID, select the volume, open the "Tags" tab, press the "Manage tags" button, press the "Add tag" button and enter a tag named "Environment" with value "Development" and press the "Save" button. Do the same for the volume of the prod instance but set the value "Production" for the "Environment" tag.

#### Steps to write a Python script that automates creating backups for production EC2 volumes

Go to the [EC2 Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#client) documentation and look for the [describe_volumes](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_volumes.html) and [create_snapshot](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/create_snapshot.html) functions.

Create a file called `volume-backups.py` with the following content:

```python
import boto3
import schedule
import time

ec2_client = boto3.client('ec2', region_name="eu-central-1")


def create_volume_snapshots():
    volumes = ec2_client.describe_volumes(
        Filters=[
            {
                'Name': 'tag:Environment',
                'Values': ['Production']
            }
        ]
    )
    for volume in volumes.get('Volumes'):
        new_snapshot = ec2_client.create_snapshot(
            VolumeId=volume.get('VolumeId')
        )
        print(f"{new_snapshot.get('StartTime')}: Created a new snapshot of volume {new_snapshot.get('VolumeId')}.")


schedule.every().day.at("03:00").do(create_volume_snapshots)

while True:
    schedule.run_pending()
    time.sleep(300) # sleep 5 minutes before checking again

```

Adjust the scheduling for testing purposes like this:
```python
schedule.every().minute.do(create_volume_snapshots)

while True:
    schedule.run_pending()
    time.sleep(1)
```

Run the script and open the AWS Management Console in the browser, navigate to the Snapshots list (link in the "Elastic Block Store" section of the menu on the left) and watch the snapshots being created. Make sure there are only snapshots of the production volume.


#### Steps to write a Python script that cleans up old EC2 volume snapshots

We want to keep only the latest two backups / snapshots. Create a file called `cleanup-snapshots.py` with the following content:

```python
import boto3

ec2_client = boto3.client('ec2', region_name="eu-central-1")

volumes = ec2_client.describe_volumes(
    Filters=[
        {
            'Name': 'tag:Environment',
            'Values': ['Production']
        }
    ]
)

for volume in volumes.get('Volumes'):
    snapshots = ec2_client.describe_snapshots(
        OwnerIds=['self'], # we only want the snapshots created by ourselves
        Filters=[
            {
                'Name': 'volume-id',
                'Values': [volume.get('VolumeId')]
            }
        ]
    )

    sorted_by_start_time = sorted(snapshots.get('Snapshots'), key=lambda snap: snap.get('StartTime'), reverse=True)
    for snap in sorted_by_start_time[2:]:
        response = ec2_client.delete_snapshot(
            SnapshotId=snap.get('SnapshotId')
        )
        print(f"HTTP status code of delete-snapshot response: {response.get('ResponseMetadata').get('HTTPStatusCode')}")
```

#### Steps to write a Python script that restores EC2 volumes

We want to create a new volume from the latest snapshot of an existing volume (which we assume got corrupted) and attach that new volume to the EC2 instance.

Create a file called `restore_volume.py` with the following content:

```python
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
```
