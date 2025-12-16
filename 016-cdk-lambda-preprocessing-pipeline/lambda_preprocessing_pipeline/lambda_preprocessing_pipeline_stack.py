from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    RemovalPolicy,
    aws_s3 as s3,
    aws_sagemaker as sagemaker,
    aws_ecr as ecr,
    aws_lambda as _lambda,
)


class LambdaPreprocessingPipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        app_prefix = "mlops-lambda-preprocessing-pipeline"

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

        """
        Create SageMaker Feature Store with Feature Groups.
        """
        # self.__create_feature_store(app_prefix)

        """
        Create ECR repository for custom processing images.
        """
        self.__create_ecr_repository(app_prefix)

        """
        Create Lambda functions for preprocessing job orchestration.
        """
        self.__create_lambda_functions(app_prefix)

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
        # Create S3 bucket for offline feature store
        self.feature_store_bucket = s3.Bucket(
            self,
            f"{app_prefix}-feature-store-bucket",
            bucket_name=f"{app_prefix}-feature-store-bucket",
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
                actions=["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
                resources=[
                    f"{self.raw_data_bucket.bucket_arn}/*",
                    f"{self.processed_data_bucket.bucket_arn}/*",
                    f"{self.model_artifacts_bucket.bucket_arn}/*",
                    f"{self.logs_bucket.bucket_arn}/*",
                    f"{self.feature_store_bucket.bucket_arn}/*",
                    self.raw_data_bucket.bucket_arn,
                    self.processed_data_bucket.bucket_arn,
                    self.model_artifacts_bucket.bucket_arn,
                    self.logs_bucket.bucket_arn,
                    self.feature_store_bucket.bucket_arn,
                ],
            )
        )

        # Add Feature Store permissions
        self.data_preprocessing_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "sagemaker:PutRecord",
                    "sagemaker:GetRecord",
                    "sagemaker:DeleteRecord",
                    "sagemaker:DescribeFeatureGroup",
                    "sagemaker:DescribeFeatureMetadata",
                    "sagemaker:BatchGetRecord",
                ],
                resources=["*"],
            )
        )

        # Add Glue permissions for Feature Store offline store
        self.data_preprocessing_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "glue:CreateTable",
                    "glue:GetTable",
                    "glue:UpdateTable",
                    "glue:DeleteTable",
                    "glue:GetDatabase",
                    "glue:CreateDatabase",
                ],
                resources=["*"],
            )
        )
    
    def __create_data_preprocessing_pipeline(self, app_prefix: str) -> None:
        """
        Create Data Preprocessing Pipeline.
        :param app_prefix: Prefix for naming resources.
        """

        pass  # Placeholder for the actual pipeline creation logic
        # We are not implementing the actual pipeline creation logic here, we are using the github action to create the pipeline.
    
    def __create_feature_store(self, app_prefix: str) -> None:
        """
        Create SageMaker Feature Store with Feature Groups based on the employee dataset.
        :param app_prefix: Prefix for naming resources.
        """

        # Define feature definitions based on transformed_data.csv columns
        feature_definitions = [
            # Record identifier - unique ID for each employee
            sagemaker.CfnFeatureGroup.FeatureDefinitionProperty(
                feature_name="employee_id",
                feature_type="String"
            ),
            # Event time - required for feature store
            sagemaker.CfnFeatureGroup.FeatureDefinitionProperty(
                feature_name="event_time",
                feature_type="String"
            ),
            # Original features from cleaned data
            sagemaker.CfnFeatureGroup.FeatureDefinitionProperty(
                feature_name="age",
                feature_type="Fractional"
            ),
            sagemaker.CfnFeatureGroup.FeatureDefinitionProperty(
                feature_name="salary",
                feature_type="Fractional"
            ),
            sagemaker.CfnFeatureGroup.FeatureDefinitionProperty(
                feature_name="department",
                feature_type="String"
            ),
            sagemaker.CfnFeatureGroup.FeatureDefinitionProperty(
                feature_name="address",
                feature_type="String"
            ),
            sagemaker.CfnFeatureGroup.FeatureDefinitionProperty(
                feature_name="phone",
                feature_type="String"
            ),
            sagemaker.CfnFeatureGroup.FeatureDefinitionProperty(
                feature_name="email",
                feature_type="String"
            ),
            # Engineered features
            sagemaker.CfnFeatureGroup.FeatureDefinitionProperty(
                feature_name="address_length",
                feature_type="Integral"
            ),
            sagemaker.CfnFeatureGroup.FeatureDefinitionProperty(
                feature_name="salary_category",
                feature_type="String"
            ),
            sagemaker.CfnFeatureGroup.FeatureDefinitionProperty(
                feature_name="age_group",
                feature_type="String"
            ),
        ]

        # Create Feature Group for employee features
        self.feature_group = sagemaker.CfnFeatureGroup(
            self,
            f"{app_prefix}-employee-feature-group",
            feature_group_name=f"{app_prefix}-employee-features",
            record_identifier_feature_name="employee_id",
            event_time_feature_name="event_time",
            feature_definitions=feature_definitions,
            # Enable online store for real-time inference
            online_store_config={
                "EnableOnlineStore": True
            },
            # Enable offline store for batch processing and training
            offline_store_config={
                "S3StorageConfig": {
                    "S3Uri": f"s3://{self.feature_store_bucket.bucket_name}/offline-store"
                },
                "DisableGlueTableCreation": False
            },
            role_arn=self.data_preprocessing_role.role_arn,
            description="Feature group for employee data with engineered features",
        )
    
    # Create ECR repository for custom processing images
    def __create_ecr_repository(self, app_prefix: str) -> None:
        """
        Create ECR repository for custom processing images.
        :param app_prefix: Prefix for naming resources.
        """
        
        self.processing_image_repository = ecr.Repository(
            self,
            f"{app_prefix}-scikit-learn",
            repository_name=f"{app_prefix}-sklearn-custom",
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True,
            image_scan_on_push=True,
        )
        
        # Grant pull permissions to the SageMaker role
        self.processing_image_repository.grant_pull(self.data_preprocessing_role)
    
    # Create Lambda functions for preprocessing job orchestration
    def __create_lambda_functions(self, app_prefix: str) -> None:
        """
        Create Lambda functions for preprocessing job orchestration.
        :param app_prefix: Prefix for naming resources.
        """

        data_preprocessing_lambda_role = iam.Role(
            self,
            f"{app_prefix}-lambda-role",
            role_name=f"{app_prefix}-lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
            ],
        )

        data_preprocessing_function = _lambda.Function(
            self,
            f"{app_prefix}-data-preprocessing-function",
            function_name=f"{app_prefix}-data-preprocessing-function",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="data_preprocessing_lambda.handler",
            code=_lambda.Code.from_asset("lambda_functions/data_preprocessing"),
            role=data_preprocessing_lambda_role,
            timeout=Duration.minutes(15),
            memory_size=512,
        )