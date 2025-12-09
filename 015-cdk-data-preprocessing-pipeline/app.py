#!/usr/bin/env python3

import aws_cdk as cdk

from data_preprocessing_pipeline.data_preprocessing_pipeline_stack import DataPreprocessingPipelineStack


app = cdk.App()
DataPreprocessingPipelineStack(app, "DataPreprocessingPipelineStack")

app.synth()
