#!/usr/bin/env python3

import aws_cdk as cdk

from sagemaker_setup.sagemaker_setup_stack import SagemakerSetupStack

app_prefix = "sagemaker-env-setup"

app = cdk.App()

SagemakerSetupStack(
    app, 
    "SagemakerSetupStack",
    app_prefix=app_prefix
)

app.synth()
