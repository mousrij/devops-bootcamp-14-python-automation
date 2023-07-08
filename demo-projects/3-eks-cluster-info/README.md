## Demo Project - Automate displaying EKS cluster information

### Topics of the Demo Project
Automate displaying EKS cluster information

### Technologies Used
- Python
- Boto3
- AWS EKS

### Project Description
- Create an EKS cluster using Terraform
- Write a Python script that fetches and displays EKS cluster status and information

#### Steps to create an EKS cluster with Terraform

Get the `terraform` folder of module 12, demo project 3 and apply it using terraform:

```sh
cd terraform

terraform init
# ...
# Terraform has been successfully initialized!

terraform apply --auto-approve
# ...
# module.eks.module.eks_managed_node_group["dev"].aws_eks_node_group.this[0]: Creation complete after 2m19s [id=myapp-eks-cluster:dev-2023070820345903730000000f]
# 
# Apply complete! Resources: 55 added, 0 changed, 0 destroyed.
```


#### Steps to write a Python script that fetches and displays EKS cluster status and information

Go to the [EKS Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/eks.html) documentation and look for the [list_clusters](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/eks/client/list_clusters.html) and the [describe_cluster](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/eks/client/describe_cluster.html) functions.

Create an `eks-status-checks.py` file with the following content:

```python
import boto3

client = boto3.client('eks', region_name="eu-central-1")
cluster_names = client.list_clusters()['clusters']

for cluster_name in cluster_names:
    response = client.describe_cluster(
        name=cluster_name
    )
    cluster_info = response['cluster']
    cluster_status = cluster_info['status']
    cluster_endpoint = cluster_info['endpoint']
    cluster_version = cluster_info['version']

    print(f"Cluster {cluster} status is {cluster_status}")
    print(f"Cluster endpoint: {cluster_endpoint}")
    print(f"Cluster version: {cluster_version}")
```

Run the script:

```sh
python3 eks-status-checks.py
# Cluster myapp-eks-cluster status is ACTIVE
# Cluster endpoint: https://27E11D5EAE37934CBB773AAE6BB4BFE4.gr7.eu-central-1.eks.amazonaws.com
# Cluster version: 1.27
```

Don't forget to cleanup and delete the cluster executing `terraform destroy` when you're done. (You can check the status with your python script while the EKS cluster is being destroyed.)
