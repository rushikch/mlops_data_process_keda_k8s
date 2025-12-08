# 🚀 Hands-On Guide: SageMaker Data Preprocessing Pipeline with CDK & GitHub Actions

## 📋 Overview

This guide demonstrates building an automated data preprocessing pipeline using AWS SageMaker Processing Jobs, AWS CDK for infrastructure, and GitHub Actions for CI/CD. You'll learn to process raw data, perform transformations, and automate the entire workflow.

## 🎯 What You'll Build

- **S3 Buckets** for raw data, processed data, model artifacts, and logs
- **IAM Roles** with fine-grained permissions for data processing
- **SageMaker Processing Job** for data preprocessing
- **GitHub Actions Workflow** for automated pipeline execution
- **Data Preprocessing Script** with cleaning and feature engineering

## 📦 Prerequisites

- AWS Account with SageMaker access
- GitHub Account
- AWS CLI configured
- Python 3.8 or higher
- Basic understanding of pandas and data processing
- Completed [013-cdk-sagemaker-setup](../013-cdk-sagemaker-setup) (optional but recommended)

## 🏗️ Architecture Overview

```
┌─────────────────┐
│  GitHub Actions │
│   (Trigger)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   SageMaker Processing Job          │
│  ┌──────────────────────────────┐   │
│  │  1. Load Data from S3        │   │
│  │  2. Clean Missing Values     │   │
│  │  3. Extract JSON Fields      │   │
│  │  4. Feature Engineering      │   │
│  │  5. Save to S3               │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│         S3 Buckets                  │
│  • Raw Data                         │
│  • Processed Data                   │
│  • Model Artifacts                  │
│  • Logs                             │
└─────────────────────────────────────┘
```

## 🛠️ Step 1: Clone Repository and Setup

### Clone the MLOps Repository

```bash
git clone https://github.com/anveshmuppeda/mlops.git
cd mlops/014-cdk-data-preprocessing-pipeline
```

### Initialize Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate.bat
```

### Install Dependencies

The `requirements.txt` file is already provided in the repository:

```bash
pip install -r requirements.txt
```

## 📝 Step 2: Review CDK Infrastructure

The CDK infrastructure is already implemented in the repository.

### Stack File

Review `data_preprocessing_pipeline/data_preprocessing_pipeline_stack.py`:

```python
from constructs import Construct
from aws_cdk import (
    Stack,
    aws_iam as iam,
    RemovalPolicy,
    aws_s3 as s3,
)

class DataPreprocessingPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        app_prefix = "mlops-data-preprocessing-pipeline"
        
        # Create S3 buckets
        self.__create_s3_buckets(app_prefix)
        
        # Create IAM roles
        self.__create_iam_roles(app_prefix)
    
    def __create_s3_buckets(self, app_prefix: str) -> None:
        # Raw data bucket
        self.raw_data_bucket = s3.Bucket(
            self,
            f"{app_prefix}-raw-data-bucket",
            bucket_name=f"{app_prefix}-raw-data-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        
        # Processed data bucket
        self.processed_data_bucket = s3.Bucket(
            self,
            f"{app_prefix}-processed-data-bucket",
            bucket_name=f"{app_prefix}-processed-data-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        
        # Model artifacts bucket
        self.model_artifacts_bucket = s3.Bucket(
            self,
            f"{app_prefix}-model-artifacts-bucket",
            bucket_name=f"{app_prefix}-model-artifacts-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        
        # Logs bucket
        self.logs_bucket = s3.Bucket(
            self,
            f"{app_prefix}-logs-bucket",
            bucket_name=f"{app_prefix}-logs-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
```

### App Entry Point

Review `app.py`:

```python
#!/usr/bin/env python3
import aws_cdk as cdk
from data_preprocessing_pipeline.data_preprocessing_pipeline_stack import DataPreprocessingPipelineStack

app = cdk.App()
DataPreprocessingPipelineStack(app, "DataPreprocessingPipelineStack")
app.synth()
```

## 🚀 Step 3: Deploy Infrastructure

### Bootstrap CDK

```bash
cdk bootstrap
```

### Deploy Stack

```bash
cdk deploy
```

This creates:
- 4 S3 buckets
- IAM role with appropriate permissions

## 📊 Step 4: Review Preprocessing Script

The preprocessing script is already provided in `data/preprocessing_script.py`:

```python
import pandas as pd
import json
import numpy as np
from datetime import datetime

# Load dataset
df = pd.read_csv('/opt/ml/processing/input/mock_data.csv')
print(f"✅ Dataset loaded successfully!")
print(f"📏 Dataset shape: {df.shape}")

# 1. Handle Missing Values
age_median = df['age'].median()
salary_median = df['salary'].median()

df['age'] = df['age'].fillna(age_median)
df['salary'] = df['salary'].fillna(salary_median)
df['department'] = df['department'].fillna('Unknown')

# 2. Extract JSON Fields
df['profile'] = df['profile'].apply(
    lambda x: json.loads(x) if pd.notnull(x) else {}
)

df['address'] = df['profile'].apply(lambda x: x.get('address', None))
df['phone'] = df['profile'].apply(lambda x: x.get('phone', None))
df['email'] = df['profile'].apply(lambda x: x.get('email', None))

# 3. Drop original profile column
cleaned_df = df.drop(columns=['profile'])

# 4. Save cleaned data
cleaned_df.to_csv("/opt/ml/processing/output/cleaned_data.csv", index=False)
print("✅ Cleaned data saved")

# 5. Feature Engineering
transform_df = pd.read_csv('/opt/ml/processing/output/cleaned_data.csv')

# Address length feature
transform_df['address_length'] = transform_df['address'].apply(
    lambda x: len(str(x))
)

# Salary categories
bins = [0, 50000, 70000, 100000]
labels = ['low', 'medium', 'high']
transform_df['salary_category'] = pd.cut(
    df['salary'], bins=bins, labels=labels, include_lowest=True
)

# Age groups
age_bins = [0, 25, 35, 45, 55, float('inf')]
age_labels = ['Young', 'Early Career', 'Mid Career', 'Senior', 'Experienced']
transform_df['age_group'] = pd.cut(
    df['age'], bins=age_bins, labels=age_labels, include_lowest=True
)

# 6. Save transformed data
transform_df.to_csv("/opt/ml/processing/output/transformed_data.csv", index=False)
print("✅ Transformed data saved")

# 7. Generate department statistics
department_stats = df.groupby('department').agg({
    'salary': 'mean',
    'age': 'mean'
}).reset_index()

department_stats.columns = ['Department', 'Average Salary', 'Average Age']
department_stats.to_csv(
    "/opt/ml/processing/output/department_statistics.csv", index=False
)
print("✅ Department statistics saved")
```

## 📤 Step 5: Upload Data and Script to S3

### Upload Mock Data

```bash
aws s3 cp data/mock_data.csv \
  s3://mlops-data-preprocessing-pipeline-raw-data-bucket/input/
```

### Upload Preprocessing Script

```bash
aws s3 cp data/preprocessing_script.py \
  s3://mlops-data-preprocessing-pipeline-model-artifacts-bucket/scripts/
```

## ⚙️ Step 6: Review Job Configuration

The job configuration template is already provided in `job-config.json`:

```json
{
  "ProcessingJobName": "{{JOB_NAME}}",
  "ProcessingInputs": [
    {
      "InputName": "input-data",
      "S3Input": {
        "S3Uri": "{{INPUT_PATH}}",
        "LocalPath": "/opt/ml/processing/input",
        "S3DataType": "S3Prefix",
        "S3InputMode": "File"
      }
    },
    {
      "InputName": "code",
      "S3Input": {
        "S3Uri": "{{SCRIPT_PATH}}",
        "LocalPath": "/opt/ml/processing/input/code",
        "S3DataType": "S3Prefix",
        "S3InputMode": "File"
      }
    }
  ],
  "ProcessingOutputConfig": {
    "Outputs": [
      {
        "OutputName": "output-data",
        "S3Output": {
          "S3Uri": "{{OUTPUT_PATH}}",
          "LocalPath": "/opt/ml/processing/output",
          "S3UploadMode": "EndOfJob"
        }
      }
    ]
  },
  "ProcessingResources": {
    "ClusterConfig": {
      "InstanceCount": 1,
      "InstanceType": "ml.t3.medium",
      "VolumeSizeInGB": 30
    }
  },
  "AppSpecification": {
    "ImageUri": "{{IMAGE_URI}}",
    "ContainerEntrypoint": [
      "python3",
      "/opt/ml/processing/input/code/preprocessing_script.py"
    ]
  },
  "RoleArn": "{{ROLE_ARN}}",
  "StoppingCondition": {
    "MaxRuntimeInSeconds": 3600
  }
}
```

## 🔄 Step 7: Review GitHub Actions Workflow

The GitHub Actions workflow is already configured in `.github/workflows/014-sagemaker-preprocessing.yml`:

### Workflow File

```yaml
name: SageMaker Preprocessing Job

on:
  workflow_dispatch:
    inputs:
      input_data_path:
        description: 'S3 path for input data'
        required: true
        default: 's3://mlops-data-preprocessing-pipeline-raw-data-bucket/input/'
      output_data_path:
        description: 'S3 path for output data'
        required: true
        default: 's3://mlops-data-preprocessing-pipeline-processed-data-bucket/output/'
  push:
    branches:
      - main
    paths:
      - 'preprocessing/**'
      - '.github/workflows/014-sagemaker-preprocessing.yml'

env:
  AWS_REGION: us-east-1
  APP_PREFIX: mlops-data-preprocessing-pipeline
  PROCESSING_INSTANCE_TYPE: ml.t3.medium
  PROCESSING_INSTANCE_COUNT: 1
  SKLEARN_VERSION: '1.2-1'

jobs:
  run-preprocessing:
    runs-on: ubuntu-latest
    
    permissions:
      id-token: write
      contents: read
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install --upgrade boto3 sagemaker>=2.0

      - name: Get SageMaker scikit-learn image URI
        id: get-image
        run: |
          ACCOUNT_ID="683313688378"
          IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${{ env.AWS_REGION }}.amazonaws.com/sagemaker-scikit-learn:${{ env.SKLEARN_VERSION }}-cpu-py3"
          echo "image_uri=${IMAGE_URI}" >> $GITHUB_OUTPUT

      - name: Generate job name with timestamp
        id: job-name
        run: |
          TIMESTAMP=$(date +%Y%m%d-%H%M%S)
          JOB_NAME="preprocessing-job-${TIMESTAMP}"
          echo "job_name=$JOB_NAME" >> $GITHUB_OUTPUT

      - name: Update SageMaker Processing Job configuration
        id: job-config
        env:
          IMAGE_URI: ${{ steps.get-image.outputs.image_uri }}
          JOB_NAME: ${{ steps.job-name.outputs.job_name }}
          INPUT_PATH: ${{ github.event.inputs.input_data_path || format('s3://{0}-raw-data-bucket/input/', env.APP_PREFIX) }}
          OUTPUT_PATH: ${{ github.event.inputs.output_data_path || format('s3://{0}-processed-data-bucket/output/', env.APP_PREFIX) }}
          SCRIPT_PATH: s3://${{ env.APP_PREFIX }}-model-artifacts-bucket/scripts/preprocessing_script.py
        run: |
          sed -e "s|{{JOB_NAME}}|$JOB_NAME|g" \
              -e "s|{{IMAGE_URI}}|$IMAGE_URI|g" \
              -e "s|{{INPUT_PATH}}|$INPUT_PATH|g" \
              -e "s|{{OUTPUT_PATH}}|$OUTPUT_PATH|g" \
              -e "s|{{SCRIPT_PATH}}|$SCRIPT_PATH|g" \
              -e "s|{{INSTANCE_COUNT}}|$PROCESSING_INSTANCE_COUNT|g" \
              -e "s|{{INSTANCE_TYPE}}|$PROCESSING_INSTANCE_TYPE|g" \
              -e "s|{{ROLE_ARN}}|arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/${{ env.APP_PREFIX }}-data-preprocessing-role|g" \
              job-config.json > job-config-final.json

      - name: Start SageMaker Processing Job
        env:
          JOB_NAME: ${{ steps.job-name.outputs.job_name }}
        run: |
          aws sagemaker create-processing-job --cli-input-json file://job-config-final.json
          echo "SageMaker processing job started: $JOB_NAME"

      - name: Wait for SageMaker Processing Job to complete
        env:
          JOB_NAME: ${{ steps.job-name.outputs.job_name }}
        run: |
          aws sagemaker wait processing-job-completed-or-stopped --processing-job-name $JOB_NAME
          
          STATUS=$(aws sagemaker describe-processing-job --processing-job-name $JOB_NAME --query 'ProcessingJobStatus' --output text)
          
          if [ "$STATUS" != "Completed" ]; then
            echo "Processing job failed"
            exit 1
          fi
```

### Configure GitHub Secrets

Go to GitHub Repository → Settings → Secrets and variables → Actions

Add secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_ACCOUNT_ID`

## 🎬 Step 8: Run the Pipeline

### Manual Trigger

1. Go to GitHub → Actions
2. Select "SageMaker Preprocessing Job"
3. Click "Run workflow"
4. Provide input/output paths (or use defaults)
5. Click "Run workflow"

### Automatic Trigger

Push changes to:
- `preprocessing/**` directory
- `.github/workflows/014-sagemaker-preprocessing.yml`

## 📊 Step 9: Monitor and Verify

### Check Job Status

```bash
aws sagemaker list-processing-jobs --max-results 10
```

### View Job Details

```bash
aws sagemaker describe-processing-job --processing-job-name <job-name>
```

### Check CloudWatch Logs

```bash
aws logs tail /aws/sagemaker/ProcessingJobs --follow
```

### Download Processed Data

```bash
aws s3 ls s3://mlops-data-preprocessing-pipeline-processed-data-bucket/output/

aws s3 cp s3://mlops-data-preprocessing-pipeline-processed-data-bucket/output/transformed_data.csv ./
```

## 📈 Step 10: Understand the Data Processing

### Input Data Structure

```csv
id,name,age,salary,hire_date,profile,department,bonus
1,Name_103,,,2025-05-16,"{""address"": ""Street 40""}",Marketing,7236.0
```

### Processing Steps

1. **Missing Value Imputation**
   - Age: Filled with median
   - Salary: Filled with median
   - Department: Filled with 'Unknown'

2. **JSON Field Extraction**
   - Extract address, phone, email from profile column
   - Drop original profile column

3. **Feature Engineering**
   - `address_length`: Length of address string
   - `salary_category`: Low/Medium/High based on salary
   - `age_group`: Young/Early Career/Mid Career/Senior/Experienced

4. **Aggregations**
   - Department-wise average salary and age

### Output Files

1. **cleaned_data.csv**: Data after missing value handling and JSON extraction
2. **transformed_data.csv**: Data with engineered features
3. **department_statistics.csv**: Aggregated department metrics

## 💰 Step 11: Cost Analysis

### Resource Costs

| Resource | Type | Cost |
|----------|------|------|
| S3 Storage | Standard | $0.023/GB/month |
| SageMaker Processing | ml.t3.medium | $0.05/hour |
| Data Transfer | Out to Internet | $0.09/GB |
| CloudWatch Logs | Storage | $0.50/GB |

### Example Calculation

For a 10-minute processing job:
- Processing: $0.05 × (10/60) = $0.0083
- S3 Storage (1GB): $0.023
- **Total**: ~$0.03 per run

### Cost Optimization Tips

1. Use spot instances for non-critical jobs
2. Compress data before uploading to S3
3. Set S3 lifecycle policies
4. Use S3 Intelligent-Tiering
5. Monitor with AWS Cost Explorer

## 🧹 Step 12: Cleanup

### Delete S3 Buckets

```bash
aws s3 rb s3://mlops-data-preprocessing-pipeline-raw-data-bucket --force
aws s3 rb s3://mlops-data-preprocessing-pipeline-processed-data-bucket --force
aws s3 rb s3://mlops-data-preprocessing-pipeline-model-artifacts-bucket --force
aws s3 rb s3://mlops-data-preprocessing-pipeline-logs-bucket --force
```

### Destroy CDK Stack

```bash
cdk destroy
```

## 🔧 Troubleshooting

### Issue: Processing Job Fails

**Check CloudWatch Logs**:
```bash
aws logs tail /aws/sagemaker/ProcessingJobs --follow
```

**Common Causes**:
- Missing input data in S3
- Incorrect script path
- Insufficient IAM permissions
- Script errors

### Issue: GitHub Actions Fails

**Check**:
- AWS credentials are correct
- Secrets are properly configured
- IAM role exists
- S3 buckets exist

### Issue: Data Not Found

**Verify**:
```bash
aws s3 ls s3://mlops-data-preprocessing-pipeline-raw-data-bucket/input/
aws s3 ls s3://mlops-data-preprocessing-pipeline-model-artifacts-bucket/scripts/
```

## 📚 Best Practices

1. **Version Control**: Keep preprocessing scripts in Git
2. **Data Validation**: Add data quality checks
3. **Error Handling**: Implement try-catch blocks
4. **Logging**: Add comprehensive logging
5. **Testing**: Test scripts locally before deployment
6. **Monitoring**: Set up CloudWatch alarms
7. **Documentation**: Document data transformations
8. **Security**: Use IAM roles, not access keys

## 🎓 Key Learnings

1. **SageMaker Processing Jobs**: Scalable data preprocessing
2. **Infrastructure as Code**: CDK for reproducible infrastructure
3. **CI/CD Integration**: GitHub Actions for automation
4. **S3 Data Management**: Organized data storage
5. **IAM Security**: Least privilege access
6. **Cost Optimization**: Understanding and managing costs

## 🔄 Next Steps

1. **Add Data Validation**: Implement Great Expectations
2. **Parallel Processing**: Use multiple instances
3. **Feature Store**: Integrate with SageMaker Feature Store
4. **Model Training**: Connect to training pipeline
5. **Monitoring**: Add data drift detection
6. **Notifications**: SNS alerts for job completion
7. **Scheduling**: Add EventBridge for scheduled runs

## 📖 Additional Resources

- [SageMaker Processing Jobs](https://docs.aws.amazon.com/sagemaker/latest/dg/processing-job.html)
- [SageMaker Python SDK](https://sagemaker.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS CDK Python Reference](https://docs.aws.amazon.com/cdk/api/v2/python/)

---

**Author**: Anvesh Muppeda  
**Project**: MLOps with AWS  
**Repository**: [github.com/anveshmuppeda/mlops](https://github.com/anveshmuppeda/mlops)
