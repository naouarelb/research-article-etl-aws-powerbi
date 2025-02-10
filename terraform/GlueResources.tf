# 1️⃣ Create the database "scopus"
resource "aws_glue_catalog_database" "scopus_database" {
  name = "scopus_database"
}

# 2️⃣ Create the crawler "scopus"
resource "aws_glue_crawler" "scopus_data_crawler" {
  name = "scopusCrawler"

  role  = aws_iam_role.scopus_transformation_role.arn
  database_name = aws_glue_catalog_database.scopus_database.name

  s3_target {
      path = "s3://${aws_s3_bucket.scopus_bucket.id}/gold/AffiliationExtractionOutput/affiliation_table/"
      
    }
  

  s3_target {
      path = "s3://${aws_s3_bucket.scopus_bucket.id}/gold/AuthorExtractionOutput/author_table/"
    }
  

  s3_target {
      path = "s3://${aws_s3_bucket.scopus_bucket.id}/gold/DocumentExtractionOutput/document_table/"
    }
  

  s3_target {
      path = "s3://${aws_s3_bucket.scopus_bucket.id}/gold/MetadataExtractionOutput/metadata_table/"
    }
  

  s3_target {
      path = "s3://${aws_s3_bucket.scopus_bucket.id}/gold/Journal Output/"
    }
  

  s3_target {
      path = "s3://${aws_s3_bucket.scopus_bucket.id}/gold/AffiliationExtractionOutput/intermediate_affiliation_metadata/"
    }
  

  s3_target {
      path = "s3://${aws_s3_bucket.scopus_bucket.id}/gold/AuthorExtractionOutput/intermediate_author_metadata/"
    }
}

# 3️⃣ Create the jobs
resource "aws_glue_job" "AffiliationExtractionJob" {
  name     = "AffiliationExtractionJob"
  role_arn = aws_iam_role.scopus_transformation_role.arn

  command {
    script_location = "s3://${aws_s3_bucket.scopus_bucket.id}/AWS Glue Jobs Scripts/AffiliationExtractionJob.py"
    python_version  = "3"
  }

  glue_version = "5.0"
  worker_type  = "G.1X"
  number_of_workers = 10

  depends_on = [
    aws_s3_bucket.scopus_bucket,
    ]
}


resource "aws_glue_job" "AuthorExtractionJob" {
  name     = "AuthorExtractionJob"
  role_arn = aws_iam_role.scopus_transformation_role.arn

  command {
    script_location = "s3://${aws_s3_bucket.scopus_bucket.id}/AWS Glue Jobs Scripts/AuthorExtractionJob.py"
    python_version  = "3"
  }

  glue_version = "5.0"
  worker_type  = "G.1X"
  number_of_workers = 10
  depends_on = [
    aws_s3_bucket.scopus_bucket,
    aws_glue_job.AffiliationExtractionJob
    ]
}


resource "aws_glue_job" "DocumentExtractionJob" {
  name     = "DocumentExtractionJob"
  role_arn = aws_iam_role.scopus_transformation_role.arn

  command {
    script_location = "s3://${aws_s3_bucket.scopus_bucket.id}/AWS Glue Jobs Scripts/DocumentExtractionJob.py"
    python_version  = "3"
  }

  worker_type  = "G.1X"
  number_of_workers = 10
  depends_on = [
    aws_s3_bucket.scopus_bucket,
    aws_glue_job.AuthorExtractionJob
    ]
}


resource "aws_glue_job" "JournalTransformationJob" {
  name     = "JournalTransformationJob"
  role_arn = aws_iam_role.scopus_transformation_role.arn

  command {
    script_location = "s3://${aws_s3_bucket.scopus_bucket.id}/AWS Glue Jobs Scripts/JournalTransformationJob.py"
    python_version  = "3"
  }

  glue_version = "5.0"
  worker_type  = "G.1X"
  number_of_workers = 10
  depends_on = [
    aws_s3_bucket.scopus_bucket,
    aws_glue_job.DocumentExtractionJob
    ]
}


resource "aws_glue_job" "CleaningJob" {
  name     = "CleaningJob"
  role_arn = aws_iam_role.scopus_transformation_role.arn

  command {
    script_location = "s3://${aws_s3_bucket.scopus_bucket.id}/AWS Glue Jobs Scripts/Cleaning.py"
    python_version  = "3"
  }

  glue_version = "5.0"
  worker_type  = "G.1X"
  number_of_workers = 10
  depends_on = [
    aws_s3_bucket.scopus_bucket,
    aws_glue_job.JournalTransformationJob
    ]
}

# 4️⃣ Create the workflow "scopus"
resource "aws_glue_workflow" "scopus_workflow" {
  name = "scopus_workflow"
}

# 5️⃣ Create the triggers for the jobs
resource "aws_glue_trigger" "DummyTrigger" {
  name       = "DummyTrigger"
  type       = "ON_DEMAND"
  workflow_name = aws_glue_workflow.scopus_workflow.name
  actions {
    job_name = aws_glue_job.AffiliationExtractionJob.name
  }
}


resource "aws_glue_trigger" "AuthorExtractionJobTrigger" {
  name       = "AuthorExtractionJobTrigger"
  type       = "CONDITIONAL"
  workflow_name = aws_glue_workflow.scopus_workflow.name
  actions {
    job_name = aws_glue_job.AuthorExtractionJob.name
  }

  predicate {
    conditions {
      job_name  = aws_glue_job.AffiliationExtractionJob.name
      state     = "SUCCEEDED"
    }
  }
}

resource "aws_glue_trigger" "DocumentExtractionJobTrigger" {
  name       = "DocumentExtractionJobTrigger"
  type       = "CONDITIONAL"
  workflow_name = aws_glue_workflow.scopus_workflow.name
  actions {
    job_name = aws_glue_job.DocumentExtractionJob.name
  }

  predicate {
    conditions {
      job_name  = aws_glue_job.AuthorExtractionJob.name
      state     = "SUCCEEDED"
    }
  }
}

resource "aws_glue_trigger" "JournalTransformationJobTrigger" {
  name       = "JournalTransformationJobTrigger"
  type       = "CONDITIONAL"
  workflow_name = aws_glue_workflow.scopus_workflow.name
  actions {
    job_name = aws_glue_job.JournalTransformationJob.name
  }

  predicate {
    conditions {
      job_name  = aws_glue_job.DocumentExtractionJob.name
      state     = "SUCCEEDED"
    }
  }
}

resource "aws_glue_trigger" "CleaningJobTrigger" {
  name       = "CleaningJobTrigger"
  type       = "CONDITIONAL"
  workflow_name = aws_glue_workflow.scopus_workflow.name
  actions {
    job_name = aws_glue_job.CleaningJob.name
  }

  predicate {
    conditions {
      job_name  = aws_glue_job.JournalTransformationJob.name
      state     = "SUCCEEDED"
    }
  }
}

resource "aws_glue_trigger" "crawlerTrigger" {
  name       = "trigger_crawler"
  type       = "CONDITIONAL"
  workflow_name = aws_glue_workflow.scopus_workflow.name
  actions {
    crawler_name = aws_glue_crawler.scopus_data_crawler.name
  }

  predicate {
    conditions {
      job_name  = aws_glue_job.CleaningJob.name
      state     = "SUCCEEDED"
    }
  }
}

