#!/bin/bash

# Create IRSA (IAM Roles for Service Accounts) with Admin Rights
# This gives the service account full AWS permissions

# Configuration - UPDATE THESE VALUES
CLUSTER_NAME="fargate-demo-cluster"
SERVICE_ACCOUNT_NAME="preprocessing-sa"
NAMESPACE="default"
AWS_REGION="us-east-1"

# Create IRSA with AdministratorAccess
eksctl create iamserviceaccount \
  --name $SERVICE_ACCOUNT_NAME \
  --namespace $NAMESPACE \
  --cluster $CLUSTER_NAME \
  --region $AWS_REGION \
  --attach-policy-arn arn:aws:iam::aws:policy/AdministratorAccess \
  --approve \
  --override-existing-serviceaccounts

# Verify creation
echo ""
echo "✅ IRSA created successfully!"
echo ""
echo "Verify with:"
echo "kubectl describe sa $SERVICE_ACCOUNT_NAME -n $NAMESPACE"