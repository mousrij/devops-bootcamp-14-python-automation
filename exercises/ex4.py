import boto3

ecr_client = boto3.client('ecr')

# Get all ECR repos and print their names
repos = ecr_client.describe_repositories().get('repositories')
for repo in repos:
    print(repo.get('repositoryName'))

print("-----------------------")

# For one specific repo, get all the images and print them out sorted by date
repo_name = "java-maven-app" # replace with your own repo-name
images = ecr_client.describe_images(
    repositoryName=repo_name
)

image_tags = []

for image in images.get('imageDetails'):
    image_tags.append({
        'tag': image.get('imageTags'),
        'pushed_at': image.get('imagePushedAt')
    })

images_sorted = sorted(image_tags, key=lambda tag: tag.get('pushed_at'), reverse=True)
for image in images_sorted:
    print(image)
