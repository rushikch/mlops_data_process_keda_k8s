# Use SageMaker's scikit-learn image as base
# For us-east-1 region
# FROM 683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3
FROM 763104351884.dkr.ecr.us-east-1.amazonaws.com/sagemaker-python:3.10
# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install additional Python packages
RUN pip install --no-cache-dir \
    sagemaker>=2.200.0 \
    boto3>=1.28.0 \
    pandas>=2.0.0 \
    numpy>=1.24.0

# Optional: Install system packages if needed
# RUN apt-get update && apt-get install -y \
#     package-name \
#     && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/ml/processing

# The entrypoint is already set in the base image