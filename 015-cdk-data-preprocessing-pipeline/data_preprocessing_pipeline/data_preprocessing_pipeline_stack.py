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

        pass  # Placeholder for the actual pipeline creation logic
        # We are not implementing the actual pipeline creation logic here, we are using the github action to create the pipeline.