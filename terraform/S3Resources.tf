# 1️⃣ Création du Bucket S3
resource "aws_s3_bucket" "scopus_bucket" {
  bucket = "scopusbucket"

  tags = {
    Name        = "scopus-bucket"
    Environment = "production"
  }
}

resource "aws_s3_bucket_policy" "scopus_bucket_policy" {
  bucket = aws_s3_bucket.scopus_bucket.id
  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::024848443352:user/MirrWear"
      },
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::scopusbucket/*"
    }
  ]
}
POLICY
}



# 2️⃣ Simulate Folders (Bronze, Silver, Gold)
resource "aws_s3_object" "bronze" {
  bucket = aws_s3_bucket.scopus_bucket.id
  key    = "bronze/"
  content = ""
}

resource "aws_s3_object" "silver" {
  bucket = aws_s3_bucket.scopus_bucket.id
  key    = "silver/"
  content = ""
}

resource "aws_s3_object" "gold" {
  bucket = aws_s3_bucket.scopus_bucket.id
  key    = "gold/"
  content = ""
}

# 3️⃣ Upload resource Files
locals {
  files = fileset("${path.module}/Resources", "*")
}

resource "aws_s3_object" "resources" {
  for_each = local.files

  bucket = aws_s3_bucket.scopus_bucket.id
  key    = "resources/${each.value}"
  source = "${path.module}/Resources/${each.value}"
  etag   = filemd5("${path.module}/Resources/${each.value}")
}


# 4️⃣ Upload Glue job's scripts
locals {
  scripts = fileset("${path.module}/AWS Glue Jobs Scripts", "*")
}

resource "aws_s3_object" "glue_scripts" {
  for_each = local.scripts

  bucket = aws_s3_bucket.scopus_bucket.id
  key    = "AWS Glue Jobs Scripts/${each.value}"
  source = "${path.module}/AWS Glue Jobs Scripts/${each.value}"
  etag   = filemd5("${path.module}/AWS Glue Jobs Scripts/${each.value}")
}