import boto3
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from pyspark.sql import SparkSession

# Create GlueContext and SparkContext
sc = SparkContext()
glueContext = GlueContext(sc)
spark = SparkSession.builder.appName("DeleteCsvAndFolderMarkers").getOrCreate()

# S3 Setup
bucket_name = "scopusbucket"
gold_prefix = "gold/"
output_analysis_prefix = "OutputAnalysis/"
s3_client = boto3.client("s3")

# Function to delete an S3 object
def delete_s3_object(key):
    print(f"Deleting: {key}")
    s3_client.delete_object(Bucket=bucket_name, Key=key)

# List all objects in the bucket (recursive)
response = s3_client.list_objects_v2(Bucket=bucket_name)

if "Contents" in response:
    for obj in response["Contents"]:
        file_key = obj["Key"]

        # 1️⃣ Delete .csv or .metadata files ONLY inside 'gold/' (not subfolders)
        if file_key.startswith(gold_prefix) and (file_key.endswith(".csv") or file_key.endswith(".metadata")):
            # Ensure it's directly inside 'gold/' and not in a subfolder
            if file_key.count("/") == gold_prefix.count("/"):
                delete_s3_object(file_key)
            else:
                print(f"Skipping subfolder file: {file_key}")

        # 2️⃣ Delete ANY file containing "_$folder$" (anywhere in the bucket)
        elif "_$folder$" in file_key:
            delete_s3_object(file_key)

        # 3️⃣ Delete all files inside "OutputAnalysis/"
        elif file_key.startswith(output_analysis_prefix):
            delete_s3_object(file_key)

    # 4️⃣ After all files inside OutputAnalysis/ are deleted, delete the "folder" marker
    folder_marker = f"{output_analysis_prefix.rstrip('/')}_$folder$"
    try:
        s3_client.head_object(Bucket=bucket_name, Key=folder_marker)
        delete_s3_object(folder_marker)
    except:
        print(f"No folder marker found: {folder_marker}")

    print("✅ Deletion completed successfully!")

else:
    print(f"No matching objects found in bucket {bucket_name}.")
