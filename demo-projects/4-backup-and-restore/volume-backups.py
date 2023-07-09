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