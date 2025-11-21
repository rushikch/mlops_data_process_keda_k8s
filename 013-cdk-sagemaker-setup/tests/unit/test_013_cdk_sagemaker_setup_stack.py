import aws_cdk as core
import aws_cdk.assertions as assertions
from 013_cdk_sagemaker_setup.013_cdk_sagemaker_setup_stack import 013CdkSagemakerSetupStack


def test_sqs_queue_created():
    app = core.App()
    stack = 013CdkSagemakerSetupStack(app, "013-cdk-sagemaker-setup")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::SQS::Queue", {
        "VisibilityTimeout": 300
    })


def test_sns_topic_created():
    app = core.App()
    stack = 013CdkSagemakerSetupStack(app, "013-cdk-sagemaker-setup")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::SNS::Topic", 1)
