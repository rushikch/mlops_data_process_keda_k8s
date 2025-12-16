"""
Lambda function for data preprocessing.
"""
import json
import boto3
import pandas as pd
import io
def handler(event, context):
    """
    Lambda function handler for data preprocessing.
    """
    s3 = boto3.client('s3')
    
    # Extract bucket and object key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    
    # Download the raw data from S3
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    raw_data = response['Body'].read().decode('utf-8')
    
    # Load the data into a pandas DataFrame
    df = pd.read_csv(io.StringIO(raw_data))
    
    # Data preprocessing steps
    # Example: Fill missing values
    df.fillna(method='ffill', inplace=True)
    
    # Example: Feature engineering - create a new feature
    df['new_feature'] = df['existing_feature'] * 2
    
    # Convert the processed DataFrame back to CSV
    processed_data = df.to_csv(index=False)
    
    # Upload the processed data back to S3
    processed_key = object_key.replace('raw', 'processed')
    s3.put_object(Bucket=bucket_name, Key=processed_key, Body=processed_data)
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Processed data uploaded to {processed_key}')
    }