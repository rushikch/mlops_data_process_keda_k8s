# 🚀 Hands-On Guide: AWS SageMaker Environment Setup with CDK

## 📋 Overview

This guide walks you through setting up a complete AWS SageMaker environment using AWS CDK (Cloud Development Kit) with Python. You'll create a production-ready infrastructure including VPC, IAM roles, SageMaker Domain, User Profile, and Notebook Instance.

## 🎯 What You'll Build

- **Custom VPC** with public and private subnets across 2 availability zones
- **IAM Roles** with appropriate permissions for SageMaker
- **SageMaker Domain** for Studio access
- **SageMaker User Profile** for team collaboration
- **SageMaker Notebook Instance** for development

## 📦 Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Python 3.8 or higher
- Node.js 14.x or higher (for CDK)
- Basic understanding of AWS services

## 🛠️ Step 1: Clone Repository and Setup

### Clone the MLOps Repository

```bash
git clone https://github.com/anveshmuppeda/mlops.git
cd mlops/013-cdk-sagemaker-setup
```

### Install AWS CDK

```bash
npm install -g aws-cdk
```

### Verify Installation

```bash
cdk --version
```

## 📝 Step 2: Setup Python Environment

### Create Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate.bat
```

### Install Dependencies

The `requirements.txt` file is already provided in the repository:

```bash
pip install -r requirements.txt
```

## 🏗️ Step 3: Review CDK Stack

The CDK stack is already implemented in the repository. Let's review the key components:

### Stack Structure

The `sagemaker_setup/sagemaker_setup_stack.py` file contains:
- VPC and networking setup
- IAM roles configuration
- SageMaker Domain and User Profile
- SageMaker Notebook Instance

### App Entry Point

The `app.py` file defines:
- App prefix: `sagemaker-env-setup`
- Stack initialization
- CDK app synthesis

You can review these files in your cloned repository.

## 🌐 Step 4: Network Configuration

The stack creates:

### VPC Configuration
- **CIDR Block**: 10.10.0.0/16
- **Public Subnets**: 10.10.0.0/24, 10.10.1.0/24
- **Private Subnets**: 10.10.10.0/24, 10.10.11.0/24
- **Internet Gateway**: For public subnet internet access
- **Route Tables**: Separate for public and private subnets

### Key Features
- DNS hostnames and support enabled
- Multi-AZ deployment for high availability
- Isolated private subnets for SageMaker resources

## 🔐 Step 5: IAM Roles Configuration

Three IAM roles are created:

### 1. SageMaker Domain Role
```
Role Name: {app_prefix}-sagemaker-domain-role
Permissions:
- AmazonSageMakerFullAccess
- AmazonS3FullAccess
- AmazonEC2FullAccess
- CloudWatchLogsFullAccess
```

### 2. SageMaker Studio User Role
```
Role Name: {app_prefix}-sagemaker-studio-user-role
Permissions: Same as Domain Role
```

### 3. SageMaker Notebook Role
```
Role Name: {app_prefix}-sagemaker-notebook-role
Permissions: Same as Domain Role
```

## 🎨 Step 6: SageMaker Resources

### SageMaker Domain
- **Auth Mode**: IAM
- **Network**: Deployed in private subnets
- **User Settings**: Configured with execution role

### SageMaker User Profile
- **User Name**: mlops-user
- **Domain**: Linked to created domain
- **Execution Role**: Studio user role

### SageMaker Notebook Instance
- **Instance Type**: ml.t3.medium
- **Network**: Private subnet with security group
- **Internet Access**: Enabled
- **Root Access**: Enabled
- **Volume Size**: 10 GB

## 🚀 Step 7: Deploy the Stack

### Bootstrap CDK (First Time Only)

```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

### Synthesize CloudFormation Template

```bash
cdk synth
```

### Review Changes

```bash
cdk diff
```

### Deploy Stack

```bash
cdk deploy
```

**Note**: Deployment takes approximately 10-15 minutes.

## ✅ Step 8: Verify Deployment

### Check SageMaker Domain

```bash
aws sagemaker list-domains
```

### Check User Profile

```bash
aws sagemaker list-user-profiles --domain-id <domain-id>
```

### Check Notebook Instance

```bash
aws sagemaker list-notebook-instances
```

### Access SageMaker Studio

1. Go to AWS Console → SageMaker
2. Click on "Domains" in left menu
3. Select your domain
4. Click "Launch" → "Studio" for mlops-user

### Access Notebook Instance

1. Go to AWS Console → SageMaker
2. Click on "Notebook instances"
3. Find your instance
4. Click "Open JupyterLab" or "Open Jupyter"

## 💰 Step 9: Cost Optimization

### Resources and Costs

| Resource | Type | Estimated Cost/Month |
|----------|------|---------------------|
| VPC | Free | $0 |
| SageMaker Domain | Free | $0 |
| Notebook Instance (ml.t3.medium) | On-Demand | ~$50 (if running 24/7) |
| Data Transfer | Variable | Depends on usage |

### Cost-Saving Tips

1. **Stop Notebook Instance** when not in use:
```bash
aws sagemaker stop-notebook-instance --notebook-instance-name <name>
```

2. **Use Lifecycle Configurations** to auto-stop instances

3. **Monitor Usage** with AWS Cost Explorer

4. **Set Budget Alerts** in AWS Budgets

## 🧹 Step 10: Cleanup

### Destroy Stack

```bash
cdk destroy
```

### Manual Cleanup (if needed)

1. Delete SageMaker Apps in Studio
2. Delete User Profiles
3. Delete SageMaker Domain
4. Delete Notebook Instance

```bash
# Stop and delete notebook instance
aws sagemaker stop-notebook-instance --notebook-instance-name <name>
aws sagemaker delete-notebook-instance --notebook-instance-name <name>

# Delete user profile
aws sagemaker delete-user-profile --domain-id <domain-id> --user-profile-name mlops-user

# Delete domain
aws sagemaker delete-domain --domain-id <domain-id>
```

## 🔧 Troubleshooting

### Issue: CDK Bootstrap Fails

**Solution**: Ensure AWS credentials are configured correctly
```bash
aws configure
aws sts get-caller-identity
```

### Issue: Deployment Timeout

**Solution**: SageMaker Domain creation can take time. Wait for completion or check CloudFormation console for detailed status.

### Issue: Insufficient Permissions

**Solution**: Ensure your IAM user/role has permissions for:
- CloudFormation
- SageMaker
- EC2
- IAM
- S3

### Issue: Notebook Instance Won't Start

**Solution**: Check:
- Security group rules
- Subnet configuration
- IAM role permissions
- CloudWatch logs for errors

## 📚 Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [SageMaker Studio User Guide](https://docs.aws.amazon.com/sagemaker/latest/dg/studio.html)
- [SageMaker Pricing](https://aws.amazon.com/sagemaker/pricing/)

## 🎓 Key Learnings

1. **Infrastructure as Code**: CDK allows version-controlled, repeatable infrastructure
2. **Network Isolation**: Private subnets provide security for ML workloads
3. **IAM Best Practices**: Separate roles for different SageMaker components
4. **Multi-AZ Deployment**: High availability for production workloads
5. **Cost Management**: Understanding resource costs and optimization strategies

## 🔄 Next Steps

1. **Customize Network**: Adjust CIDR blocks and subnet configurations
2. **Add NAT Gateway**: Enable private subnet internet access (commented in code)
3. **Implement Lifecycle Policies**: Auto-stop/start notebook instances
4. **Add Monitoring**: CloudWatch dashboards and alarms
5. **Integrate with CI/CD**: Automate deployments with GitHub Actions

## 📝 Notes

- The NAT Gateway is commented out to reduce costs. Uncomment if private subnets need internet access.
- Security groups allow all traffic for demonstration. Restrict in production.
- Consider using AWS Secrets Manager for sensitive configurations.
- Implement tagging strategy for resource management and cost allocation.

---

**Author**: Anvesh Muppeda  
**Project**: MLOps with AWS  
**Repository**: [github.com/anveshmuppeda/mlops](https://github.com/anveshmuppeda/mlops)
