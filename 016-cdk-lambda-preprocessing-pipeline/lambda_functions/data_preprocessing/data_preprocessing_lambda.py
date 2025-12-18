"""
Lambda function for triggering SageMaker data preprocessing jobs.
"""
import json
import boto3
import os
from datetime import datetime

sagemaker_client = boto3.client('sagemaker')
s3_client = boto3.client('s3')

def handler(event, context):
    """
    Lambda function handler for triggering SageMaker preprocessing jobs.
    Supports both S3 event triggers and manual invocations.
    """
    
    # Configuration from environment variables
    app_prefix = os.environ.get('APP_PREFIX', 'mlops-lambda-preprocessing-pipeline')
    aws_region = os.environ.get('AWS_REGION', 'us-east-1')
    processing_instance_type = os.environ.get('PROCESSING_INSTANCE_TYPE', 'ml.t3.medium')
    processing_instance_count = int(os.environ.get('PROCESSING_INSTANCE_COUNT', '1'))
    sklearn_version = os.environ.get('SKLEARN_VERSION', '1.2-1')
    role_arn = os.environ.get('SAGEMAKER_ROLE_ARN')
    
    # Determine input/output paths
    if 'Records' in event:
        # Triggered by S3 event
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        object_key = event['Records'][0]['s3']['object']['key']
        input_data_path = f's3://{bucket_name}/{os.path.dirname(object_key)}/'
        output_data_path = f's3://{app_prefix}-processed-data-bucket/output/'
    else:
        # Manual invocation with parameters
        input_data_path = event.get('input_data_path', f's3://{app_prefix}-raw-data-bucket/input/')
        output_data_path = event.get('output_data_path', f's3://{app_prefix}-processed-data-bucket/output/')
    
    # Generate unique job name with timestamp
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    job_name = f'preprocessing-job-{timestamp}'
    
    # Get SageMaker scikit-learn image URI
    account_id = "683313688378"  # SageMaker account for us-east-1
    image_uri = f"{account_id}.dkr.ecr.{aws_region}.amazonaws.com/sagemaker-scikit-learn:{sklearn_version}-cpu-py3"
    
    # Script location in S3
    script_path = f's3://{app_prefix}-model-artifacts-bucket/scripts/preprocessing_script.py'
    
    try:
        # Create SageMaker Processing Job
        response = sagemaker_client.create_processing_job(
            ProcessingJobName=job_name,
            RoleArn=role_arn,
            AppSpecification={
                'ImageUri': image_uri,
                'ContainerEntrypoint': [
                    'python3',
                    '/opt/ml/processing/input/code/preprocessing_script.py'
                ]
            },
            ProcessingInputs=[
                {
                    'InputName': 'input-data',
                    'S3Input': {
                        'S3Uri': input_data_path,
                        'LocalPath': '/opt/ml/processing/input',
                        'S3DataType': 'S3Prefix',
                        'S3InputMode': 'File',
                        'S3DataDistributionType': 'FullyReplicated'
                    }
                },
                {
                    'InputName': 'code',
                    'S3Input': {
                        'S3Uri': script_path,
                        'LocalPath': '/opt/ml/processing/input/code',
                        'S3DataType': 'S3Prefix',
                        'S3InputMode': 'File',
                        'S3DataDistributionType': 'FullyReplicated'
                    }
                }
            ],
            ProcessingOutputConfig={
                'Outputs': [
                    {
                        'OutputName': 'output-data',
                        'S3Output': {
                            'S3Uri': output_data_path,
                            'LocalPath': '/opt/ml/processing/output',
                            'S3UploadMode': 'EndOfJob'
                        }
                    }
                ]
            },
            ProcessingResources={
                'ClusterConfig': {
                    'InstanceCount': processing_instance_count,
                    'InstanceType': processing_instance_type,
                    'VolumeSizeInGB': 30
                }
            },
            StoppingCondition={
                'MaxRuntimeInSeconds': 3600  # 1 hour timeout
            },
            Tags=[
                {
                    'Key': 'Project',
                    'Value': app_prefix
                },
                {
                    'Key': 'ManagedBy',
                    'Value': 'Lambda'
                }
            ]
        )
        
        job_arn = response['ProcessingJobArn']
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'SageMaker processing job started successfully',
                'job_name': job_name,
                'job_arn': job_arn,
                'input_path': input_data_path,
                'output_path': output_data_path,
                'console_url': f'https://console.aws.amazon.com/sagemaker/home?region={aws_region}#/processing-jobs/{job_name}'
            })
        }
        
    except Exception as e:
        print(f"Error creating SageMaker processing job: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to create SageMaker processing job',
                'error': str(e)
            })
        }