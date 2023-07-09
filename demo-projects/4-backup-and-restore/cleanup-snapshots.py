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
