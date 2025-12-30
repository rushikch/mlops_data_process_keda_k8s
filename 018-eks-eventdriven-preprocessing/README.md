# MLOps on Kubernetes: EKS Data Preprocessing with Pod Identity
### A hands-on guide to building scalable ML data processing pipelines on Amazon EKS with secure AWS service integration

## Overview

This comprehensive guide demonstrates building a **production-grade MLOps data preprocessing pipeline** on Amazon EKS that combines:
- **Amazon EKS** for container orchestration
- **EKS Pod Identity** for secure AWS service access
- **SageMaker Containers** for ML-optimized processing
- **CDK Infrastructure** for reproducible deployments
- **Kubernetes Manifests** for workload management

## What You'll Build

![EKS MLOps Architecture](./img/15-mlops-eks-preprocessing.png)

### Architecture Components

1. **EKS Cluster** - Managed Kubernetes control plane
2. **Pod Identity Agent** - Secure AWS service authentication
3. **Data Processing Pods** - SageMaker container-based workloads
4. **S3 Integration** - Secure data input/output operations
5. **VPC Networking** - Multi-AZ public/private subnet architecture
6. **IAM Security** - Fine-grained permissions with Pod Identity

## Prerequisites

- AWS Account with EKS, S3, and IAM permissions
- AWS CLI configured with appropriate credentials
- kubectl installed and configured
- Python 3.8+ and Node.js 18+ for CDK
- Docker knowledge for container understanding
- Basic Kubernetes concepts familiarity

## Step 1: Clone Repository and Setup

### Clone the MLOps Repository

```bash
git clone https://github.com/anveshmuppeda/mlops.git
cd mlops/017-eks-preprocessing
```

### Setup CDK Environment

```bash
cd cdk-eks-cluster-stack
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Install CDK Dependencies

```bash
npm install -g aws-cdk
cdk --version
```

## Step 2: Understanding the CDK Infrastructure

### Network Stack Architecture

The `network_stack.py` creates a robust VPC foundation:

```python
# VPC with custom CIDR
self.vpc = ec2.Vpc(
    vpc_name=f"{app_prefix}-vpc",
    ip_addresses=ec2.IpAddresses.cidr("10.10.0.0/16"),
    enable_dns_hostnames=True,
    enable_dns_support=True
)

# Public subnets for EKS nodes
for i, az in enumerate(azs):
    subnet = ec2.CfnSubnet(
        availability_zone=az,
        cidr_block=f"10.10.{i}.0/24",
        map_public_ip_on_launch=True
    )
```

### EKS Cluster Configuration

The `eks_cluster_stack.py` creates a production-ready EKS cluster:

```python
# EKS Cluster with Pod Identity
self.cluster = eks.Cluster(
    cluster_name=f"{app_prefix}-eks-cluster",
    version=eks.KubernetesVersion.V1_32,
    vpc=self.network_stack.vpc,
    endpoint_access=eks.EndpointAccess.PUBLIC,
    cluster_logging=[
        eks.ClusterLoggingTypes.API,
        eks.ClusterLoggingTypes.AUTHENTICATOR,
        eks.ClusterLoggingTypes.AUDIT
    ]
)
```

### Key Infrastructure Components

| Component | Purpose | Configuration |
|-----------|---------|---------------|
| **VPC** | Network isolation | 10.10.0.0/16 CIDR |
| **Public Subnets** | EKS node placement | Multi-AZ deployment |
| **Private Subnets** | Future workloads | NAT Gateway access |
| **EKS Cluster** | Container orchestration | Kubernetes 1.32 |
| **Node Group** | Compute capacity | t3.medium instances |
| **Pod Identity** | AWS service access | Secure authentication |

## Step 3: IAM Roles and Pod Identity Setup

### Data Processing Role

The CDK creates a specialized IAM role for Pod Identity:

```python
self.data_preprocessing_role = iam.Role(
    role_name=f"{app_prefix}-data-preprocessing-role",
    assumed_by=iam.PrincipalWithConditions(
        iam.ServicePrincipal("pods.eks.amazonaws.com"),
        conditions={}
    ).with_session_tags(),
    managed_policies=[
        iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
        iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess")
    ]
)
```

### Pod Identity Association

```python
self.pod_identity_association = eks.CfnPodIdentityAssociation(
    cluster_name=self.cluster.cluster_name,
    namespace="mlops",
    role_arn=self.data_preprocessing_role.role_arn,
    service_account="data-preprocessing-sa"
)
```

### S3 Buckets for MLOps Pipeline

```python
# Raw data storage
self.raw_data_bucket = s3.Bucket(
    bucket_name=f"{app_prefix}-raw-data-bucket",
    removal_policy=RemovalPolicy.DESTROY,
    auto_delete_objects=True
)

# Processed data output
self.processed_data_bucket = s3.Bucket(
    bucket_name=f"{app_prefix}-processed-data-bucket",
    removal_policy=RemovalPolicy.DESTROY,
    auto_delete_objects=True
)
```

## Step 4: Deploy the EKS Infrastructure

### Bootstrap CDK (First Time Only)

```bash
cdk bootstrap
```

### Deploy the Network Stack

```bash
cdk deploy NetworkStack
```

### Deploy the EKS Stack

```bash
cdk deploy EksClusterStack
```

### Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name eks-demo-eks-cluster
```

### Verify Cluster Access

```bash
kubectl get nodes
kubectl get pods -A
```

## Step 5: Understanding the Kubernetes Manifests

### Service Account Configuration

The `deployment.yaml` creates a service account for Pod Identity:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: data-preprocessing-sa
  namespace: mlops
```

### Deployment Specification

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-preprocessing
  namespace: mlops
spec:
  replicas: 1
  template:
    spec:
      serviceAccountName: data-preprocessing-sa
      containers:
      - name: preprocessing
        image: 683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.4-2-cpu-py3
        env:
        - name: INPUT_BUCKET
          value: "eks-demo-raw-data-bucket"
        - name: OUTPUT_BUCKET
          value: "eks-demo-processed-data-bucket"
        - name: AWS_DEFAULT_REGION
          value: "us-east-1"
```

### Processing Script ConfigMap

The `cm.yaml` contains the data preprocessing logic:

```python
# Upgrade boto3 for Pod Identity support
subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "boto3>=1.28.0"])

# Initialize S3 client with Pod Identity
s3_client = boto3.client('s3')

# Download data from S3
s3_client.download_file(input_bucket, input_key, local_input)

# Process data (cleaning, transformation, feature engineering)
df = pd.read_csv(local_input)
# ... processing logic ...

# Upload results back to S3
s3_client.upload_file(local_file, output_bucket, s3_key)
```

## Step 6: Deploy the Processing Pipeline

### Create MLOps Namespace

```bash
kubectl create namespace mlops
```

### Upload Sample Data

```bash
# Upload mock data to S3
aws s3 cp data/mock_data.csv s3://eks-demo-raw-data-bucket/data/
```

### Deploy Kubernetes Manifests

```bash
kubectl apply -f manifests/cm.yaml
kubectl apply -f manifests/deployment.yaml
```

### Verify Pod Identity Setup

```bash
# Check Pod Identity addon
aws eks describe-addon --cluster-name eks-demo-eks-cluster --addon-name eks-pod-identity-agent

# Verify Pod Identity associations
aws eks list-pod-identity-associations --cluster-name eks-demo-eks-cluster

# Check Pod Identity Agent pods
kubectl get pods -n kube-system | grep pod-identity
```

## Step 7: Monitor Processing Execution

### Watch Pod Status

```bash
kubectl get pods -n mlops -w
```

### View Processing Logs

```bash
kubectl logs -f deployment/data-preprocessing -n mlops
```

### Expected Log Output

```
📦 Upgrading boto3 to support EKS Pod Identity...
✅ boto3 upgraded successfully
🔐 Initializing AWS S3 client with EKS Pod Identity...
✅ S3 client initialized successfully
📥 Downloading s3://eks-demo-raw-data-bucket/data/mock_data.csv
✅ Dataset loaded: (50000, 8)
📊 Filling missing values...
🔧 Extracting profile fields...
✅ Saved: cleaned_data.csv
✅ Saved: transformed_data.csv
📤 Uploading to s3://eks-demo-processed-data-bucket/output/cleaned_data_20241221-224904.csv
✅ Preprocessing completed successfully!
```

### Verify Output Data

```bash
# Check processed data in S3
aws s3 ls s3://eks-demo-processed-data-bucket/output/ --recursive

# Download and inspect results
aws s3 cp s3://eks-demo-processed-data-bucket/output/cleaned_data_20241221-224904.csv ./
```

## Step 8: Understanding Pod Identity Authentication

### How Pod Identity Works

1. **Pod Identity Agent** runs as DaemonSet on each node
2. **Service Account** is associated with IAM role
3. **Pods** automatically get AWS credentials via agent
4. **boto3** discovers credentials through metadata endpoint

### Pod Identity vs IRSA Comparison

| Feature | Pod Identity | IRSA |
|---------|-------------|------|
| **Setup Complexity** | Simple | Complex (OIDC) |
| **Token Management** | Automatic | Manual rotation |
| **Cross-Account** | Supported | Limited |
| **Credential Caching** | Built-in | Manual |
| **Performance** | Optimized | Standard |

### Troubleshooting Pod Identity

```bash
# Check Pod Identity Agent logs
kubectl logs -n kube-system -l app.kubernetes.io/name=eks-pod-identity-agent

# Verify agent endpoint
kubectl exec -n mlops deployment/data-preprocessing -- curl -s http://169.254.170.23/v1/credentials

# Check service account annotations
kubectl describe sa data-preprocessing-sa -n mlops
```

## Step 9: Advanced Processing Configurations

### Resource Management

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### Environment Variables

```yaml
env:
- name: PROCESSING_MODE
  value: "batch"
- name: LOG_LEVEL
  value: "INFO"
- name: PARALLEL_WORKERS
  value: "4"
```

### Volume Mounts for Large Data

```yaml
volumeMounts:
- name: data-volume
  mountPath: /opt/ml/processing/data
volumes:
- name: data-volume
  emptyDir:
    sizeLimit: "10Gi"
```

## Step 10: Cost Optimization Strategies

### Spot Instances for Node Groups

```python
# Add to CDK node group configuration
capacity_type=eks.CapacityType.SPOT,
instance_types=[
    ec2.InstanceType("t3.medium"),
    ec2.InstanceType("t3a.medium"),
    ec2.InstanceType("m5.large")
]
```

### Vertical Pod Autoscaler

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: data-preprocessing-vpa
  namespace: mlops
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: data-preprocessing
  updatePolicy:
    updateMode: "Auto"
```

### Resource Quotas

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mlops-quota
  namespace: mlops
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "10"
```

## Step 11: Troubleshooting Guide

### Common Issues and Solutions

#### Issue: Pod Identity Authentication Fails

**Symptoms**: `ValueError: Unsupported host '169.254.170.23'`
**Solution**: Upgrade boto3 in the container
```python
subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "boto3>=1.28.0"])
```

#### Issue: Pod Stuck in Pending State

**Symptoms**: Pod remains in Pending status
**Solution**: Check node capacity and resource requests
```bash
kubectl describe pod <pod-name> -n mlops
kubectl top nodes
```

#### Issue: S3 Access Denied

**Symptoms**: `AccessDenied` errors when accessing S3
**Solution**: Verify Pod Identity association
```bash
aws eks describe-pod-identity-association --cluster-name eks-demo-eks-cluster --association-id <id>
```

#### Issue: Container Image Pull Errors

**Symptoms**: `ImagePullBackOff` status
**Solution**: Verify ECR permissions and image availability
```bash
aws ecr describe-images --repository-name sagemaker-scikit-learn
```

### Debug Commands

```bash
# Check cluster status
kubectl cluster-info

# Verify Pod Identity agent
kubectl get daemonset eks-pod-identity-agent -n kube-system

# Check pod logs
kubectl logs -f deployment/data-preprocessing -n mlops --previous

# Describe pod for events
kubectl describe pod <pod-name> -n mlops

# Check service account
kubectl get sa data-preprocessing-sa -n mlops -o yaml
```

## Step 12: Production Deployment Checklist

### Security Hardening

- [ ] Enable Pod Security Standards
- [ ] Implement Network Policies
- [ ] Use private subnets for worker nodes
- [ ] Enable VPC Flow Logs
- [ ] Configure AWS Config rules
- [ ] Implement secrets encryption at rest

### Monitoring Setup

- [ ] Deploy CloudWatch Container Insights
- [ ] Configure Prometheus/Grafana
- [ ] Set up alerting rules
- [ ] Implement log aggregation
- [ ] Configure distributed tracing

### High Availability

- [ ] Multi-AZ node group deployment
- [ ] Pod Disruption Budgets
- [ ] Cluster autoscaler configuration
- [ ] Backup and disaster recovery plan

### Performance Optimization

- [ ] Resource requests and limits
- [ ] Horizontal Pod Autoscaler
- [ ] Vertical Pod Autoscaler
- [ ] Node affinity rules
- [ ] Spot instance integration

## Step 13: Cleanup Resources

### Delete Kubernetes Resources

```bash
kubectl delete namespace mlops
```

### Remove S3 Objects

```bash
aws s3 rm s3://eks-demo-raw-data-bucket --recursive
aws s3 rm s3://eks-demo-processed-data-bucket --recursive
```

### Destroy CDK Stacks

```bash
cdk destroy EksClusterStack
cdk destroy NetworkStack
```

### Verify Cleanup

```bash
aws eks list-clusters
aws s3 ls | grep eks-demo
aws ec2 describe-vpcs --filters "Name=tag:Application,Values=eks-demo"
```

## Key Learnings and Best Practices

### Architecture Benefits

1. **Kubernetes-Native MLOps** - Container orchestration for ML workloads
2. **Secure AWS Integration** - Pod Identity for seamless service access
3. **Scalable Processing** - Horizontal and vertical scaling capabilities
4. **Cost Optimization** - Spot instances and autoscaling
5. **Production Ready** - Monitoring, security, and reliability features

### Technical Concepts Mastered

1. **EKS Cluster Management** - Control plane and worker node configuration
2. **Pod Identity Authentication** - Secure AWS service access without keys
3. **Container Orchestration** - Kubernetes deployments and services
4. **Infrastructure as Code** - CDK for reproducible deployments
5. **MLOps Pipeline Design** - Data processing workflow automation

### Production Considerations

1. **Security First** - Network policies, Pod Security Standards, IAM least privilege
2. **Observability** - Comprehensive monitoring and logging
3. **Reliability** - High availability and disaster recovery
4. **Performance** - Resource optimization and autoscaling
5. **Cost Management** - Spot instances and resource quotas

### MLOps Best Practices

1. **Container-First Approach** - Consistent runtime environments
2. **Declarative Configuration** - Kubernetes manifests for reproducibility
3. **Secure by Design** - Pod Identity and network isolation
4. **Scalable Architecture** - Auto-scaling based on demand
5. **GitOps Integration** - Version-controlled deployments

## Next Steps and Extensions

### Immediate Enhancements

1. **Add Data Validation** - Schema validation and data quality checks
2. **Implement Job Queues** - Kubernetes Jobs for batch processing
3. **Add Model Training** - Extend pipeline to include training workflows
4. **Integrate Feature Store** - SageMaker Feature Store integration

### Advanced Features

1. **Multi-Tenant Architecture** - Namespace isolation for different teams
2. **GPU Workloads** - NVIDIA device plugin for ML training
3. **Serverless Integration** - Knative for event-driven processing
4. **Service Mesh** - Istio for advanced traffic management
5. **ML Experiment Tracking** - MLflow or Kubeflow integration

### Integration Opportunities

1. **Apache Airflow** - Workflow orchestration on Kubernetes
2. **Spark on Kubernetes** - Large-scale data processing
3. **Ray Cluster** - Distributed ML training and inference
4. **Argo Workflows** - Complex ML pipeline orchestration
5. **Tekton Pipelines** - Cloud-native CI/CD for ML

## Summary

This EKS-based MLOps pipeline demonstrates:

✅ **Kubernetes-Native MLOps** - Container orchestration for ML workloads  
✅ **Secure AWS Integration** - Pod Identity for seamless service access  
✅ **Scalable Architecture** - Auto-scaling based on processing demands  
✅ **Production Security** - Network policies and Pod Security Standards  
✅ **Infrastructure as Code** - CDK for reproducible deployments  
✅ **Cost Optimization** - Spot instances and resource management  
✅ **Comprehensive Monitoring** - CloudWatch and Prometheus integration  

The pipeline automatically processes data using SageMaker containers on EKS, with secure AWS service access via Pod Identity, demonstrating a modern approach to MLOps that combines the flexibility of Kubernetes with the power of AWS ML services.

---

**Author**: Anvesh Muppeda  
**Project**: MLOps with AWS  
**Repository**: [github.com/anveshmuppeda/mlops](https://github.com/anveshmuppeda/mlops)  
**Blog**: [Medium @muppedaanvesh](https://medium.com/@muppedaanvesh)