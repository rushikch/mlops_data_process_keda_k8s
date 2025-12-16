#!/usr/bin/env python3

import aws_cdk as cdk

from lambda_preprocessing_pipeline.lambda_preprocessing_pipeline_stack import LambdaPreprocessingPipelineStack


app = cdk.App()
LambdaPreprocessingPipelineStack(app, "LambdaPreprocessingPipelineStack")
app.synth()
