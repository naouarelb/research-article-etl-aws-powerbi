import sys
import re
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import split, explode, col, udf, monotonically_increasing_id, collect_list, concat_ws, first
from pyspark.sql.types import StructType, StructField, StringType, ArrayType
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, regexp_replace

# Initialize the Glue Context, Spark Context, and the Job
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Define the schema for the city JSON file
cities_schema = StructType([
    StructField("standardized_city", StringType(), True),
    StructField("variations", ArrayType(StringType()), True)
])

# Define the schema for the university JSON file
uni_schema = StructType([
    StructField("standardized_uni", StringType(), True),
    StructField("variations", ArrayType(StringType()), True)
])

# Corrected schema for school JSON file
school_schema = StructType([
    StructField("school", StringType(), True),
    StructField("university", StringType(), True),
    StructField("city", StringType(), True),
    StructField("variations", ArrayType(StringType()), True)  # Corrected to ArrayType(StringType)
])

# Load the shool.json file from S3
school_mapping = spark.read.schema(school_schema).option("multiline", True).json("s3://scopusbucket/resources/school.json")
school_mapping = school_mapping.rdd.map(lambda row: (row.school, (row.university, row.city, row.variations))).collectAsMap()

# Load the city.json file from s3
cities_mapping = spark.read.schema(cities_schema).option("multiline", True).json("s3://scopusbucket/resources/city.json")
cities_mapping = cities_mapping.rdd.map(lambda row: (row.standardized_city, row.variations)).collectAsMap()

# Load the university.json file from S3
uni_mapping = spark.read.schema(uni_schema).option("multiline", True).json("s3://scopusbucket/resources/university.json")
uni_mapping = uni_mapping.rdd.map(lambda row: (row.standardized_uni, row.variations)).collectAsMap()

# load all CSV files in the silver folder
input_dynamic_frame = glueContext.create_dynamic_frame.from_options(
    format_options={
        "withHeader": True,
        "separator": "|",
    },
    connection_type="s3",
    format="csv",
    connection_options={
        "paths": ["s3://scopusbucket/silver/"],
        "recurse": True
    },
    transformation_ctx="input_dynamic_frame"
)


# Convert DynamicFrame to Spark DataFrame
dataframe = input_dynamic_frame.toDF()

# Add a unique row_id to dataframe DataFrame
dataframe = dataframe.withColumn("row_id", monotonically_increasing_id())

# Explode the "Affiliations" column into multiple rows
exploded_affiliations_df = dataframe.withColumn(
    "Affiliation", explode(split(col("Affiliations"), ";"))
)

# Define functions to extract school, university, city and country

def extract_city(affiliation):
    normalized_affiliation = re.sub(r"[^\w\s]", " ", affiliation)
    normalized_affiliation = re.sub(r"\s+", " ", normalized_affiliation).strip().lower()
    for standardized_city, variations in cities_mapping.items():
        if variations is None:
            continue
        for variation in variations:
            if variation is None:
                continue
            variation_lower = variation.lower()
            if variation_lower in normalized_affiliation:
                return standardized_city
    return None

def extract_country(affiliation):
    if "morocco" in affiliation.lower() or "maroc" in affiliation.lower():
        return "Morocco"
    return None

def extract_university(affiliation):
    normalized_affiliation = re.sub(r"[^\w\s]", " ", affiliation)
    normalized_affiliation = re.sub(r"\s+", " ", normalized_affiliation).strip().lower()
    for standardized_uni, variations in uni_mapping.items():
        if variations is None:
            continue
        for variation in variations:
            if variation is None:
                continue
            variation_lower = variation.lower()
            if variation_lower in normalized_affiliation:
                return standardized_uni
    return None

def extract_school(affiliation):
    city = extract_city(affiliation)
    university = extract_university(affiliation)
    if not city or not university:
        return None
    normalized_affiliation = affiliation.replace(",", " ")
    normalized_affiliation = re.sub(r"\s+", " ", normalized_affiliation).strip().lower()   
    for school, (entry_uni, entry_city, variations) in school_mapping.items():
        # Check if the city and university match
        if entry_city.lower() == city.lower() and entry_uni.lower() == university.lower():
            # Check if any variation exists in the affiliation
            for variation in variations:
                if re.search(rf"(^|\s){re.escape(variation.lower())}($|\s)", normalized_affiliation):
                    return school
    return None

# Define the main function to process affiliations
def process_affiliations(affiliation):
    city = extract_city(affiliation)
    country = extract_country(affiliation)
    university = extract_university(affiliation)
    school = extract_school(affiliation)
    return (school, university, city, country)


# Register the function as a UDF
schema = StructType([
    StructField("school", StringType(), True),
    StructField("university", StringType(), True),
    StructField("city", StringType(), True),
    StructField("country", StringType(), True)
])

process_affiliations_udf = udf(process_affiliations, schema)

# Apply the UDF to process affiliations
processed_affiliations_df = exploded_affiliations_df.withColumn(
    "processed_affiliation", process_affiliations_udf(col("Affiliation"))
).select(
    col("*"),
    col("processed_affiliation.school").alias("school"),
    col("processed_affiliation.university").alias("university"),
    col("processed_affiliation.city").alias("city"),
    col("processed_affiliation.country").alias("country")
).drop("processed_affiliation")

# Create the Affiliation Table
affiliation_table = processed_affiliations_df.select(
    col("Affiliation").alias("affiliation"),
    col("school"),
    col("university"),
    col("city"),
    col("country")
).distinct()

# Add a sequential affiliate_id using row_number()
window_spec = Window.orderBy("affiliation")
affiliation_table = affiliation_table.withColumn(
    "affiliate_id", row_number().over(window_spec)
)

# Select columns for Affiliation Table
affiliation_table = affiliation_table.select(
    col("affiliate_id"),
    col("affiliation"),
    col("university"),
    col("school"),
    col("city"),
    col("country")
    )

# Add affiliate_id to exploded_affiliations_df (Join the two dataframes by affiliation to add column affiliate_if to the main dataframe)
exploded_with_fk = exploded_affiliations_df.alias("exploded").join(
    affiliation_table.alias("aff"),
    exploded_affiliations_df["Affiliation"] == affiliation_table["affiliation"],
    "left"
).select(
    col("exploded.*"),
    col("aff.affiliate_id")
)

# Re-aggregate the data back to its original structure
reaggregated_df = exploded_with_fk.groupBy("row_id").agg(
    collect_list("affiliate_id").alias("affiliate_ids"),
    *[first(col(c)).alias(c) for c in dataframe.columns if c != "Affiliations" and c != "row_id"]
)

# generate the dataframe that would serve as the intermadiate tabel between metadata and affiliation
intermediate_affiliation_metadata = exploded_with_fk.select("row_id", "affiliate_id").distinct()

reaggregated_df = reaggregated_df.drop(
    "Cited by",
    "Authors with affiliations", 
    "Molecular Sequence Numbers",
    "Chemicals/CAS",
    "Tradenames",
    "Manufacturers",
    "Funding Details",
    "Funding Texts",
    "Correspondence Address",
    "Editors",
    "Publisher",
    "Sponsors",
    "Conference name",
    "Conference date",
    "Conference location",
    "Conference code",
    "ISBN",
    "CODEN",
    "PubMed ID",
    "Abbreviated Source Title",
    "affiliate_ids"
)
# Define columns required in the final metadata DataFrame
required_columns = [
    "row_id",  # Now unambiguous
    "authors", "author full names", "author(s) id", "title", "year", "source title", "volume", "issue", "art_no", 
    "page start", "page end", "page count", "doi", "link", "affiliations", "abstract", 
    "author keywords", "index keywords", "references", "issn", "language of original document", 
    "document type", "publication stage", "open access", "source", "eid"
]
required_columns_lower = [col.lower() for col in required_columns]

# Convert column names to lowercase
reaggregated_df_lower = reaggregated_df.toDF(*[col.lower() for col in reaggregated_df.columns])

# Select the required columns, including row_id
original_with_fk = reaggregated_df_lower.select(
    *[col(c) for c in required_columns_lower if c in reaggregated_df_lower.columns]
)

# Clean both Affiliation Table dataframe and original dataframe
for column_name in affiliation_table.columns:
    affiliation_table = affiliation_table.withColumn(
        column_name, regexp_replace(col(column_name), '"', '')
    )
for column_name in original_with_fk.columns:
    original_with_fk = original_with_fk.withColumn(
        column_name, regexp_replace(col(column_name), '"', '')
    )
for column_name in intermediate_affiliation_metadata.columns:
    intermediate_affiliation_metadata = intermediate_affiliation_metadata.withColumn(
        column_name, regexp_replace(col(column_name), '"', '')
    )

    
# Write the dataframes with foreign keys to S3
affiliation_table.repartition(1).write.csv(
    path="s3://scopusbucket/gold/AffiliationExtractionOutput/affiliation_table/", 
    mode="overwrite", 
    header=True, 
    sep="|"
)
original_with_fk.repartition(1).write.csv(
    path="s3://scopusbucket/gold/AffiliationExtractionOutput/metadata_table/", 
    mode="overwrite", 
    header=True, 
    sep="|"
)
intermediate_affiliation_metadata.repartition(1).write.csv(
    path="s3://scopusbucket/gold/AffiliationExtractionOutput/intermediate_affiliation_metadata/",
    mode="overwrite",
    header=True,
    sep="|"
)

# Commit the job
job.commit()