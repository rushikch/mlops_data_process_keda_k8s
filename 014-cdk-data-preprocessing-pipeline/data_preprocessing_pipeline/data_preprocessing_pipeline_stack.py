from constructs import Construct
from aws_cdk import (
    Stack,
    aws_iam as iam,
    RemovalPolicy,
    aws_s3 as s3,
    aws_sagemaker as sagemaker,
)


class DataPreprocessingPipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        app_prefix = "mlops-data-preprocessing-pipeline"

        """
        Create required S3 buckets for data preprocessing pipeline.
        """
        self.__create_s3_buckets(app_prefix)

        """
        Create IAM roles for data preprocessing tasks.
        """
        self.__create_iam_roles(app_prefix)

        """
        Create Data Preprocessing Pipeline
        """
        self.__create_data_preprocessing_pipeline(app_prefix)

    def __create_s3_buckets(self, app_prefix: str) -> None:
        """
        Create S3 buckets for raw data, processed data, model artifacts, and logs.
        :param app_prefix: Prefix for naming resources.
        """

        self.raw_data_bucket = s3.Bucket(
            self,
            f"{app_prefix}-raw-data-bucket",
            bucket_name=f"{app_prefix}-raw-data-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        self.processed_data_bucket = s3.Bucket(
            self,
            f"{app_prefix}-processed-data-bucket",
            bucket_name=f"{app_prefix}-processed-data-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        self.model_artifacts_bucket = s3.Bucket(
            self,
            f"{app_prefix}-model-artifacts-bucket",
            bucket_name=f"{app_prefix}-model-artifacts-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        self.logs_bucket = s3.Bucket(
            self,
            f"{app_prefix}-logs-bucket",
            bucket_name=f"{app_prefix}-logs-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
    
    def __create_iam_roles(self, app_prefix: str) -> None:
        """
        Create IAM roles for data preprocessing tasks.
        :param app_prefix: Prefix for naming resources.
        """

        self.data_preprocessing_role = iam.Role(
            self,
            f"{app_prefix}-data-preprocessing-role",
            role_name=f"{app_prefix}-data-preprocessing-role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess"),
            ],
        )

        # Add inline policy for S3 bucket access
        self.data_preprocessing_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
                resources=[
                    f"{self.raw_data_bucket.bucket_arn}/*",
                    f"{self.processed_data_bucket.bucket_arn}/*",
                    f"{self.model_artifacts_bucket.bucket_arn}/*",
                    f"{self.logs_bucket.bucket_arn}/*",
                ],
            )
        )
    
    def __create_data_preprocessing_pipeline(self, app_prefix: str) -> None:
        """
        Create Data Preprocessing Pipeline.
        :param app_prefix: Prefix for naming resources.
        """
        # Create Processing Job
        self.processing_job = sagemaker.CfnProcessingJob(
            self,
            "DataProcessingJob",
            processing_job_name=f"{app_prefix}-data-preprocessing-job",
            role_arn=self.data_preprocessing_role.role_arn,
            
            # App Specification - using SKLearn container
            app_specification=sagemaker.CfnProcessingJob.AppSpecificationProperty(
                image_uri=f"246618743249.dkr.ecr.{self.region}.amazonaws.com/sagemaker-scikit-learn:1.0-1-cpu-py3",
            ),
            
            # Processing Inputs
            processing_inputs=[
                # Input 1: Raw data from raw-data bucket
                sagemaker.CfnProcessingJob.ProcessingInputsObjectProperty(
                    input_name="raw-data",
                    s3_input=sagemaker.CfnProcessingJob.S3InputProperty(
                        s3_uri=f"s3://{self.raw_data_bucket.bucket_name}/input/",
                        s3_data_type="S3Prefix",
                        local_path="/opt/ml/processing/input/data",
                        s3_input_mode="File",
                    )
                ),
                # Input 2: Preprocessing code from processed-data bucket
                sagemaker.CfnProcessingJob.ProcessingInputsObjectProperty(
                    input_name="preprocessing-code",
                    s3_input=sagemaker.CfnProcessingJob.S3InputProperty(
                        s3_uri=f"s3://{self.processed_data_bucket.bucket_name}/code/preprocessing.py",
                        s3_data_type="S3Prefix",
                        local_path="/opt/ml/processing/input/code",
                        s3_input_mode="File",
                    )
                )
            ],
            
            # Processing Outputs - all to processed-data bucket with different prefixes
            processing_output_config=sagemaker.CfnProcessingJob.ProcessingOutputConfigProperty(
                outputs=[
                    # Output 1: Training data
                    sagemaker.CfnProcessingJob.ProcessingOutputsObjectProperty(
                        output_name="train-data",
                        s3_output=sagemaker.CfnProcessingJob.S3OutputProperty(
                            s3_uri=f"s3://{self.processed_data_bucket.bucket_name}/train/",
                            s3_upload_mode="EndOfJob",
                            local_path="/opt/ml/processing/output/train"
                        )
                    ),
                    # Output 2: Test data
                    sagemaker.CfnProcessingJob.ProcessingOutputsObjectProperty(
                        output_name="test-data",
                        s3_output=sagemaker.CfnProcessingJob.S3OutputProperty(
                            s3_uri=f"s3://{self.processed_data_bucket.bucket_name}/test/",
                            s3_upload_mode="EndOfJob",
                            local_path="/opt/ml/processing/output/test"
                        )
                    ),
                    # Output 3: Processing metrics/logs to logs bucket
                    sagemaker.CfnProcessingJob.ProcessingOutputsObjectProperty(
                        output_name="processing-logs",
                        s3_output=sagemaker.CfnProcessingJob.S3OutputProperty(
                            s3_uri=f"s3://{self.logs_bucket.bucket_name}/processing-jobs/",
                            s3_upload_mode="EndOfJob",
                            local_path="/opt/ml/processing/output/logs"
                        )
                    )
                ]
            ),
            
            # Processing Resources
            processing_resources=sagemaker.CfnProcessingJob.ProcessingResourcesProperty(
                cluster_config=sagemaker.CfnProcessingJob.ClusterConfigProperty(
                    instance_count=1,
                    instance_type="ml.t3.medium",
                    volume_size_in_gb=30
                )
            ),
            
            # Stopping Condition
            stopping_condition=sagemaker.CfnProcessingJob.StoppingConditionProperty(
                max_runtime_in_seconds=3600
            ),
            
            # Environment variables
            environment={
                "RAW_DATA_BUCKET": self.raw_data_bucket.bucket_name,
                "PROCESSED_DATA_BUCKET": self.processed_data_bucket.bucket_name,
                "MODEL_ARTIFACTS_BUCKET": self.model_artifacts_bucket.bucket_name,
                "LOGS_BUCKET": self.logs_bucket.bucket_name
            },
            
            tags=[{"key": "Name", "value": f"{app_prefix}-processing-job"}]
        )