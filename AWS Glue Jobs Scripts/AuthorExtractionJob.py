import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.types import StructType, StructField, StringType
from pyspark.sql import functions as F

# Initialize the Glue Context, Spark Context, and the Job
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)


# Register the function as a UDF
schema = StructType([
    StructField("author id", StringType(), True),
    StructField("author name", StringType(), True)
])

# Read the combined CSV file from S3
input_dynamic_frame = glueContext.create_dynamic_frame.from_options(
    format_options={
        "withHeader": True,
        "separator": "|",
    },
    connection_type="s3",
    format="csv",
    connection_options={
        "paths": ["s3://scopusbucket/gold/AffiliationExtractionOutput/metadata_table/"],
        "recurse": True
    },
    transformation_ctx="input_dynamic_frame"
)


# Convert DynamicFrame to Spark DataFrame
dataframe = input_dynamic_frame.toDF()

# Explode the "author full names" column into multiple rows
exploded_df = dataframe.withColumn(
    "author_entry", 
    F.explode(F.split(F.col("author full names"), ";"))
)

# Extract author names and ids (distinct ids)
split_df = exploded_df.withColumn(
    "author_name", 
    F.regexp_replace(
        F.regexp_extract(F.col("author_entry"), r"^(.*?)\s*\(\d+\)$", 1), 
        ",", 
        ""
    )
).withColumn(
    "author_id", 
    F.regexp_extract(F.trim(F.col("author_entry")), r"^.*?\((\d+)\)$", 1)
).dropDuplicates(["author_id"])

# Create the author table
author_table = split_df.select("author_name", "author_id").distinct()

# Drop unnecessary columns
rest_df = split_df.drop("authors", "author full names", "author_entry", "author(s) id")

intemediate_author_metadata = rest_df.select("row_id", "author_id")


# Group by all columns except the last two (author_name and author_id) and Aggregating the last two columns (author_name and author_id) using collect_list
aggregated_df = rest_df.groupBy(rest_df.columns[:-2]).agg(
    F.collect_list("author_name").alias("author_names"),
    F.collect_list("author_id").alias("author_ids")
)


aggregated_df = aggregated_df.drop("author_ids", "author_names")

# Write both dataframes to S3
author_table.repartition(1).write.csv(path="s3://scopusbucket/gold/AuthorExtractionOutput/author_table/", mode="overwrite", header=True, sep="|")
aggregated_df.repartition(1).write.csv(path="s3://scopusbucket/gold/AuthorExtractionOutput/metadata_table/", mode="overwrite", header=True, sep="|")
intemediate_author_metadata.repartition(1).write.csv(path="s3://scopusbucket/gold/AuthorExtractionOutput/intermediate_author_metadata", mode="overwrite", header=True, sep="|")
# Commit the job
job.commit()