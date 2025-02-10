import sys
import re
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, regexp_replace


# Initialize the Glue Context, Spark Context, and the Job
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read the combined CSV file from S3
input_dynamic_frame = glueContext.create_dynamic_frame.from_options(
    format_options={
        "withHeader": True,
        "separator": "|",
    },
    connection_type="s3",
    format="csv",
    connection_options={
        "paths": ["s3://scopusbucket/gold/AuthorExtractionOutput/metadata_table/"],
        "recurse": True
    },
    transformation_ctx="input_dynamic_frame"
)

# Convert DynamicFrame to Spark DataFrame
dataframe = input_dynamic_frame.toDF()

# Select columns of Document dataframe
doc_df = dataframe.select(
    regexp_replace(col("eid"), r"^2-s2\.0-", "").alias("doc_id"),
    "doi",
    "title",
    "document type",
    "volume", 
    "issue", 
    "art_no", 
    "page start", 
    "page end", 
    "page count", 
    "link", 
    "abstract", 
    "issn", 
    "language of original document",
    "author keywords",
    "references"
).dropDuplicates(["doc_id"]).filter(col("doc_id").cast("double").isNotNull())


# Select columns of Metadata dataframe
original_df_fk = dataframe.select(
    regexp_replace(col("eid"), r"^2-s2\.0-", "").alias("doc_id"),
    *[col for col in dataframe.columns if col not in [
        "title", "volume", "issue", "art_no", "page start", "page end", 
        "page count", "link", "abstract", "issn", "language of original document", "doi", "isbn", "references", "eid", "document type","author keywords"
    ]]
).filter(col("doc_id").cast("double").isNotNull())


# Clean the dataframes
for column_name in original_df_fk.columns:
    original_df_fk = original_df_fk.withColumn(
        column_name, regexp_replace(col(column_name), '"', '')
    )
for column_name in doc_df.columns:
    doc_df = doc_df.withColumn(
        column_name, regexp_replace(col(column_name), '"', '')
    )

# Write the document Table and metadata to S3
doc_df.repartition(1).write.csv(path="s3://scopusbucket/gold/DocumentExtractionOutput/document_table/", mode="overwrite", header=True, sep="|")
original_df_fk.repartition(1).write.csv(path="s3://scopusbucket/gold/MetadataExtractionOutput/metadata_table/", mode="overwrite", header=True, sep="|")

# Commit the job
job.commit()