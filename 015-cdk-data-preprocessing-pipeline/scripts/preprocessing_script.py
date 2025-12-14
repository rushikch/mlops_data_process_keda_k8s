import pandas as pd
import sys
import os
import json
import numpy as np
from datetime import datetime
import logging
import boto3
from sagemaker.feature_store.feature_group import FeatureGroup
import sagemaker
import time

# Setup logging to write to both console and file
log_dir = '/opt/ml/processing/logs'
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, 'preprocessing.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize SageMaker session and Feature Store client (FIXED)
region = (
    os.environ.get("AWS_REGION")
    or os.environ.get("AWS_DEFAULT_REGION")
    or "us-east-1"
)

boto_sess = boto3.Session(region_name=region)
sagemaker_session = sagemaker.Session(boto_session=boto_sess)

logger.info(f"Initialized SageMaker session in region: {region}")
print(f"✅ Initialized SageMaker session in region: {region}")

# Load dataset
try:
    df = pd.read_csv('/opt/ml/processing/input/mock_data.csv')
    logger.info(f"✅ Dataset loaded successfully!")
    logger.info(f"📏 Dataset shape: {df.shape}")
    print(f"✅ Dataset loaded successfully!")
    print(f"📏 Dataset shape: {df.shape}")
except FileNotFoundError:
    logger.error("❌ Error: mock_data.csv not found")
    print("❌ Error: mock_data.csv not found. Please run create_dataset.py first.")
    exit()

# Analyze missing patterns
print("\n📊 Missing Value Patterns:")
print("Missing Age values:")
print(df[df['age'].isnull()][['age', 'salary', 'department']])

print("Missing Salary values")
print(df[df['salary'].isnull()][['age', 'salary', 'department']])

# Get the median values for age, and salary
age_median = df['age'].median()
salary_median = df['salary'].median()
print("Age Median", age_median)
print("Salary Median", salary_median)

# Fill missing values of age with age_median
df['age'] = df['age'].fillna(age_median)
# Fill missing values of salary with salary_median
df['salary'] = df['salary'].fillna(salary_median)

# Verify the Age & Salary data
df.head()
# Check for missing values
print("Missing values in each column")
df.isnull().sum()

print("Print the missing values for Department\n")
print("Missing Department Missing values")
print(df[df['department'].isnull()][['age', 'salary', 'department']])

# Fill the missing values in department with 'Unknown'
df['department'] = df['department'].fillna('Unknown')

# Verify the Age & Salary data
df.head()
# Check for missing values
print("Missing values in each column")
print(df.isnull().sum())
# Check unique values in the department column
df['department'].unique()

print("Top rows from profile column \n")
print(df['profile'].head())

# Find the first non-null value in the column
profile_first_value = df['profile'].dropna().iloc[0]
# Print its type
print("\nProfile column values current data type")
print(type(profile_first_value))

# If your 'profile' column already contains Python dictionaries, not JSON strings.
# You do not need to parse it with json.loads(). The data is ready to be used directly.

# Convert profile JSON strings into dictionaries
df['profile'] = df['profile'].apply(lambda x: json.loads(x) if pd.notnull(x) else {})

# Extract Address Field
print("Extract Address Field....\n")
# Create new 'address' column by extracting from 'profile' dictionaries
df['address'] = df['profile'].apply(lambda x: x.get('address', None))  # Returns None if no address key

print("Top rows from profile column \n")
print(df['profile'].head())
print("\nTop rows from newly created address column \n")
print(df['address'].head())

# Extract Phone Field
print("Extract Phone Field....\n")
# Create new 'phone' column by extracting from 'profile' dictionaries
df['phone'] = df['profile'].apply(lambda x: x.get('phone', None))  # Returns None if no address key

print("Top rows from profile column \n")
print(df['profile'].head())
print("\nTop rows from newly created phone column \n")
print(df['phone'].head())

# Extract Email Field
print("Extract Email Field....\n")
# Create new 'email' column by extracting from 'profile' dictionaries
df['email'] = df['profile'].apply(lambda x: x.get('email', None))  # Returns None if no address key

print("Top rows from profile column \n")
print(df['profile'].head())
print("\nTop rows from newly created email column \n")
print(df['email'].head())

print(f"\n✅ Profile fields extracted:")


# Now drop the profile column
print("\nColumns before dropping profile:")
print(df.columns.tolist())

# Without inplace=True (df remains unchanged)
cleaned_df = df.drop(columns=['profile'])

# With inplace=True (df is modified directly)
#df.drop(columns=['profile'], inplace=True)

print("\nColumns in new DataFrame after dropping profile:")
# print(df.columns.tolist())
print(cleaned_df.columns.tolist())

print("\n💾 Saving cleaned data to: 'data/cleaned_data.csv' ...")
cleaned_df.to_csv("/opt/ml/processing/output/cleaned_data.csv", index=False)
print("✅ Cleaned data saved to: '/opt/ml/processing/output/cleaned_data.csv'")

transform_df = pd.read_csv('/opt/ml/processing/output/cleaned_data.csv')
transform_df.head()

# Create a new column 'address_length' 
print("\n🔧 Creating Address Length Feature...")
transform_df['address_length'] = transform_df['address'].apply(lambda x: len(str(x)))
print("Address followed by Address Length columns")
transform_df[['address', 'address_length']].head()

print("\n🔧 Creating Salary Categories...")
# Define the bins and labels
bins = [0, 50000, 70000, 100000]
labels = ['low', 'medium', 'high']

# Create a new column 'salary_category'
transform_df['salary_category'] = pd.cut(df['salary'], bins=bins, labels=labels, include_lowest=True)

# Print sample data after adding the 'salary_category' column
print("Sample data after adding the 'salary_category' column: \n")
transform_df[['salary', 'salary_category']].head()

print("\n🔧 Creating Age Groups...")
# Define age bins and labels
age_bins = [0, 25, 35, 45, 55, float('inf')]
age_labels = ['Young', 'Early Career', 'Mid Career', 'Senior', 'Experienced']

# Create a new column 'salary_category'
transform_df['age_group'] = pd.cut(df['age'], bins=age_bins, labels=age_labels, include_lowest=True)

# Age group distribution
print(f"Age group distribution:")
print(transform_df['age_group'].value_counts())

# Print sample data after adding the 'salary_category' column
print("\nSample data after adding the 'age_group' column: \n")
transform_df[['age', 'age_group']].head()

print("\n🔧 Creating Department Statistics...")
# Group by 'department' and calculate average salary and age
department_summary_report = df.groupby('department').agg({
    'salary': 'mean',
    'age': 'mean'
}).reset_index()

# rename columns of department_summary_report for clarity
department_summary_report.columns = ['Department', 'Average Salary', 'Average Age']

# Print the Summary Report
print("Summary report of average salary and age based on the department:\n")
print(department_summary_report)


print("\n📊 Data Quality Metrics...")

quality_metrics = {
    'total_rows': len(transform_df),
    'total_columns': len(transform_df.columns),
    'missing_values_count': transform_df.isnull().sum().sum(),
    'duplicate_rows': transform_df.duplicated().sum(),
    'numeric_columns': len(transform_df.select_dtypes(include=[np.number]).columns),
    'categorical_columns': len(transform_df.select_dtypes(include=['object']).columns),
    'unique_departments': transform_df['department'].nunique(),
    'unique_age_groups': transform_df['age_group'].nunique(),
    'unique_salary_categories': transform_df['salary_category'].nunique(),
    'processing_timestamp': datetime.now().isoformat()
}

print("Data Quality Metrics:")
for metric, value in quality_metrics.items():
    print(f"  {metric}: {value}")

print("Saving Transformed data csv to: '/opt/ml/processing/output/transformed_data.csv' ...")
transform_df.to_csv("/opt/ml/processing/output/transformed_data.csv", index=False)
print("\nTransformed data csv saved to: '/opt/ml/processing/output/transformed_data.csv'")

### Step 2: Save Department Statistics
print("Saving department statistics...")
department_summary_report.to_csv("/opt/ml/processing/output/department_statistics.csv", index=False)
print("✅ Department statistics saved to: '/opt/ml/processing/output/department_statistics.csv'")

# ==================== FEATURE STORE INGESTION ====================
print("\n" + "="*60)
print("🏪 STARTING FEATURE STORE INGESTION")
print("="*60)

try:
    # Prepare data for Feature Store
    feature_store_df = transform_df.copy()
    
    # Add required columns for Feature Store
    # 1. employee_id - unique identifier (using index)
    feature_store_df['employee_id'] = feature_store_df.index.astype(str)
    
    # 2. event_time - timestamp in ISO format (required by Feature Store)
    current_time = datetime.now()
    feature_store_df['event_time'] = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Convert categorical columns to string
    feature_store_df['salary_category'] = feature_store_df['salary_category'].astype(str)
    feature_store_df['age_group'] = feature_store_df['age_group'].astype(str)
    feature_store_df['department'] = feature_store_df['department'].astype(str)
    feature_store_df['address'] = feature_store_df['address'].astype(str)
    feature_store_df['phone'] = feature_store_df['phone'].astype(str)
    feature_store_df['email'] = feature_store_df['email'].astype(str)
    
    # Ensure numeric columns are float
    feature_store_df['age'] = feature_store_df['age'].astype(float)
    feature_store_df['salary'] = feature_store_df['salary'].astype(float)
    
    # Ensure address_length is integer
    feature_store_df['address_length'] = feature_store_df['address_length'].astype(int)
    
    # Select only the columns that match the feature store schema
    feature_columns = [
        'employee_id',
        'event_time',
        'age',
        'salary',
        'department',
        'address',
        'phone',
        'email',
        'address_length',
        'salary_category',
        'age_group'
    ]
    
    feature_store_df = feature_store_df[feature_columns]
    
    print(f"\n📋 Feature Store DataFrame Info:")
    print(f"Shape: {feature_store_df.shape}")
    print(f"Columns: {feature_store_df.columns.tolist()}")
    print(f"\nFirst few rows:")
    print(feature_store_df.head())
    print(f"\nData types:")
    print(feature_store_df.dtypes)
    
    # Get Feature Group name from environment variable or use default
    feature_group_name = os.environ.get(
        'FEATURE_GROUP_NAME', 
        'mlops-data-preprocessing-pipeline-employee-features'
    )
    
    logger.info(f"Connecting to Feature Group: {feature_group_name}")
    print(f"\n🔗 Connecting to Feature Group: {feature_group_name}")
    
    # Initialize Feature Group
    feature_group = FeatureGroup(
        name=feature_group_name,
        sagemaker_session=sagemaker_session
    )
    
    # Wait for feature group to be created (if it's being created concurrently)
    print(f"\n⏳ Waiting for Feature Group to be available...")
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            status = feature_group.describe()['FeatureGroupStatus']
            logger.info(f"Feature Group status: {status}")
            
            if status == 'Created':
                print(f"✅ Feature Group is ready!")
                break
            elif status == 'Creating':
                print(f"⏳ Feature Group is still being created... (attempt {retry_count + 1}/{max_retries})")
                time.sleep(30)
                retry_count += 1
            else:
                logger.warning(f"Unexpected Feature Group status: {status}")
                time.sleep(30)
                retry_count += 1
        except Exception as e:
            logger.warning(f"Error checking Feature Group status (attempt {retry_count + 1}/{max_retries}): {str(e)}")
            time.sleep(30)
            retry_count += 1
    
    if retry_count >= max_retries:
        raise Exception("Feature Group did not become available within the expected time")
    
    # Ingest data into Feature Store
    print(f"\n📤 Ingesting {len(feature_store_df)} records into Feature Store...")
    logger.info(f"Starting ingestion of {len(feature_store_df)} records")
    
    feature_group.ingest(
        data_frame=feature_store_df,
        max_workers=3,
        wait=True
    )
    
    print(f"✅ Successfully ingested {len(feature_store_df)} records into Feature Store!")
    logger.info(f"Successfully ingested {len(feature_store_df)} records into Feature Store")
    
    # Save Feature Store DataFrame for verification
    feature_store_output_path = "/opt/ml/processing/output/feature_store_data.csv"
    feature_store_df.to_csv(feature_store_output_path, index=False)
    print(f"✅ Feature Store data saved to: {feature_store_output_path}")
    
    # Log ingestion metrics
    ingestion_metrics = {
        'feature_group_name': feature_group_name,
        'records_ingested': len(feature_store_df),
        'ingestion_timestamp': current_time.isoformat(),
        'features_count': len(feature_columns),
        'region': region
    }
    
    print(f"\n📊 Feature Store Ingestion Metrics:")
    for metric, value in ingestion_metrics.items():
        print(f"  {metric}: {value}")
        logger.info(f"{metric}: {value}")
    
except Exception as e:
    logger.error(f"❌ Error during Feature Store ingestion: {str(e)}")
    print(f"\n❌ Error during Feature Store ingestion: {str(e)}")
    print("⚠️  Continuing with local file outputs...")
    # Don't exit, allow the job to complete with file outputs

print("\n" + "="*60)
print("🏪 FEATURE STORE INGESTION COMPLETED")
print("="*60)

# Write final summary to log file
logger.info("=" * 50)
logger.info("PROCESSING JOB COMPLETED SUCCESSFULLY")
logger.info("=" * 50)
logger.info(f"Total rows processed: {len(transform_df)}")
logger.info(f"Output files created: 4 (including feature_store_data.csv)")
logger.info(f"Log file location: {log_file}")
logger.info("=" * 50)