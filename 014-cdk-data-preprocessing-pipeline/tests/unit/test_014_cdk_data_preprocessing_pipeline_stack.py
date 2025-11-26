import aws_cdk as core
import aws_cdk.assertions as assertions
from 014_cdk_data_preprocessing_pipeline.014_cdk_data_preprocessing_pipeline_stack import 014CdkDataPreprocessingPipelineStack


def test_sqs_queue_created():
    app = core.App()
    stack = 014CdkDataPreprocessingPipelineStack(app, "014-cdk-data-preprocessing-pipeline")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::SQS::Queue", {
        "VisibilityTimeout": 300
    })


def test_sns_topic_created():
    app = core.App()
    stack = 014CdkDataPreprocessingPipelineStack(app, "014-cdk-data-preprocessing-pipeline")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::SNS::Topic", 1)
