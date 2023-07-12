import requests
import smtplib
import os
import paramiko
import linode_api4
import time
import schedule

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
LINODE_TOKEN = os.environ.get('LINODE_TOKEN')


def send_notification(email_msg):
    print('Sending an email...')
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.ehlo()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        message = f"Subject: SITE DOWN\n{email_msg}"
        smtp.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, message)


def restart_container():
    print('Restarting the application...')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname='194.233.169.74', username='root', key_filename='/Users/fsiegrist/.ssh/id_ed25519')
   
    # get the container id of the nginx container
    stdin, stdout, stderr = ssh.exec_command("docker ps -a | grep nginx | awk '{split($0,a); print a[1]}'")
    container_id = stdout.readline()
    print(f"nginx container id = {container_id}")
   
    # stop the nginx container
    print("stopping the nginx container...")
    stdin, stdout, stderr = ssh.exec_command(f"docker stop {container_id}")
    print(stdout.readlines())

    time.sleep(2)

    # restart the nginx container
    print("starting the nginx container...")
    stdin, stdout, stderr = ssh.exec_command(f"docker start {container_id}")
    print(stdout.readlines())
    ssh.close()


def restart_server_and_container():
    # restart linode server
    linode_id = 47625059
    print(f"Rebooting the server with Linode ID {linode_id}...")
    client = linode_api4.LinodeClient(LINODE_TOKEN)
    nginx_server = client.load(linode_api4.Instance, linode_id)
    nginx_server.reboot()

    # restart the application
    while True:
        nginx_server = client.load(linode_api4.Instance, linode_id)
        if nginx_server.status == 'running':
            time.sleep(5)
            restart_container()
            break


def monitor_application():
    try:
        response = requests.get('http://194.233.169.74:8080/')
        if response.status_code == 200:
            print('Application is running successfully!')
        else:
            print('Application Down. Fix it!')
            msg = f"Application returned {response.status_code}"
            send_notification(msg)
            restart_container()
    except Exception as ex:
        print(f"Connection error happened: {ex}")
        msg = 'Application not accessible at all'
        send_notification(msg)
        restart_server_and_container()

schedule.every(5).minutes.do(monitor_application)

while True:
    schedule.run_pending()
    time.sleep(10)
