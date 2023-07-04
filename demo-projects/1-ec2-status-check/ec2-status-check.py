import boto3
import schedule
import time

ec2_client = boto3.client('ec2', region_name="eu-central-1")

# reservations = ec2_client.describe_instances()
# for reservation in reservations.get('Reservations'):
#     instances = reservation.get('Instances')
#     for instance in instances:
#         print(f"Instance {instance.get('InstanceId')} is {instance.get('State').get('Name')}")

def check_instance_status():
    statuses = ec2_client.describe_instance_status(
        IncludeAllInstances=True # needed to get the status of all instances, not just the running ones
    )
    for status in statuses.get('InstanceStatuses'):
        ins_status = status.get('InstanceStatus').get('Status')
        sys_status = status.get('SystemStatus').get('Status')
        state = status.get('InstanceState').get('Name')
        print(f"Instance {status.get('InstanceId')} is {state} with instance status {ins_status} and system status {sys_status}")
        
    print("==================\n")


schedule.every(5).seconds.do(check_instance_status)

while True:
    schedule.run_pending()
    time.sleep(1)
