import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.types import IntegerType
from pyspark.sql.functions import regexp_replace, col , split

# Initialize the Glue Context, Spark Context, and the Job
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read the journal CSV file from S3
input_dynamic_frame = glueContext.create_dynamic_frame.from_options(
    format_options={
        "withHeader": True,
        "separator": ",",
        "quoteChar": '"'
    },
    connection_type="s3",
    format="csv",
    connection_options={
        "paths": ["s3://scopusbucket/bronze/Journal/raw/"],
        "recurse": True
    },
    transformation_ctx="input_dynamic_frame"
)

# Convert DynamicFrame to Spark DataFrame
dataframe = input_dynamic_frame.toDF()


# Define the journal dataframe
journal_df = dataframe.select(
    col("Sourceid"),
    col("Title"),
    col("Type"),
    col("Issn").alias("Issn Online"),
    col("SJR"),
    col("SJR Best Quartile"),
    col("H index"),
    col("`Total Docs. (2023)`").alias("Total Docs 2023"),
    col("`Total Docs. (3years)`").alias("Total Docs Last 3 years"),
    col("`Total Refs.`").alias("Total Refs"),
    col("`Total Cites (3years)`").alias("Total Cites Last 3 years"),
    col("`Citable Docs. (3years)`").alias("Citable Docs Last 3 years"),
    col("`Cites / Doc. (2years)`").alias("Citations Over Docs Last 2 Years"),
    col("`Ref. / Doc.`").alias("Ref Over Docs"),
    col("%Female"),
    col("Overton"),
    col("SDG"),
    col("Country"),
    col("Region"),
    col("Publisher"),
    col("Categories"),
    col("Areas")
    ).dropDuplicates(["Issn Online"])

# Delete all occurence of the pipe | so that there won't be any problems with the seperator
journal_df = journal_df.select([regexp_replace(col, '\|', '').alias(col) for col in journal_df.columns])

# Drop unneeded columns (Rank, coverage)
journal_df = journal_df.drop("Rank", "Coverage")
journal_df = journal_df.filter(
    col("H index").rlike("^[0-9]+$"))
    

journal_df = journal_df \
    .withColumn("SJR", regexp_replace(col("SJR"), ",", ".")) \
    .withColumn("%Female", regexp_replace(col("%Female"), ",", ".")) \
    .withColumn("Ref Over Docs", regexp_replace(col("Ref Over Docs"), ",", ".")) \
    .withColumn("Citations Over Docs Last 2 Years", regexp_replace(col("Citations Over Docs Last 2 Years"), ",", "."))

journal_df = journal_df.withColumn("H index", journal_df["H index"].cast(IntegerType()))

journal_df = journal_df.withColumn("Issn Online", split(col("Issn Online"), ",").getItem(0))

# Step 13: Repartition and write the Affiliation Table to S3
journal_df.repartition(1).write.csv(
    path="s3://scopusbucket/gold/Journal Output/", 
    mode="overwrite", 
    header=True, 
    sep="|",
    quote=''
)



# Commit the job
job.commit()