import aws_cdk as core
import aws_cdk.assertions as assertions
from 016_cdk_lambda_preprocessing_pipeline.016_cdk_lambda_preprocessing_pipeline_stack import 016CdkLambdaPreprocessingPipelineStack


def test_sqs_queue_created():
    app = core.App()
    stack = 016CdkLambdaPreprocessingPipelineStack(app, "016-cdk-lambda-preprocessing-pipeline")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::SQS::Queue", {
        "VisibilityTimeout": 300
    })


def test_sns_topic_created():
    app = core.App()
    stack = 016CdkLambdaPreprocessingPipelineStack(app, "016-cdk-lambda-preprocessing-pipeline")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::SNS::Topic", 1)
