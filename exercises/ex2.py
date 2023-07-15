import boto3

iam_client = boto3.client('iam')

iam_users = iam_client.list_users().get('Users')
last_active_user = iam_users[0]

for iam_user in iam_users:
    print(f"{iam_user.get('UserName')} -> last active: {iam_user.get('PasswordLastUsed')}")
    if last_active_user.get('PasswordLastUsed') < iam_user.get('PasswordLastUsed'):
        last_active_user = iam_user

print("\n")
print("Last active user:")
print(f"{last_active_user.get('UserId')}: {last_active_user.get('UserName')} -> last active: {last_active_user.get('PasswordLastUsed')}")
