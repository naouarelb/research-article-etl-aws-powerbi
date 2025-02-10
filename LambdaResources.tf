# 1️⃣ AWS Lambda Function (Using Predefined IAM Role)
resource "aws_lambda_function" "scopusfunction" {
  function_name = "TransformationScopus"
  role          = aws_iam_role.scopus_transformation_role.arn
  runtime       = "python3.13"
  handler       = "main.lambda_handler"

  # Upload source code directly
  filename         = "LambdaCode\lambda.zip"
  source_code_hash = filebase64sha256("lambda.zip")

  publish       = false

  memory_size   = 3008
  timeout       = 900

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.scopus_bucket.id
    }
  }
}

data "aws_lambda_invocation" "test" {
  function_name = aws_lambda_function.scopusfunction.function_name

  input = jsonencode({})
}


# 2️⃣ S3 Event Trigger (Triggers Lambda When a .zip File is Added to bronze/)
resource "aws_s3_bucket_notification" "s3_trigger" {
  bucket = aws_s3_bucket.scopus_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.scopusfunction.arn
    events              = ["s3:ObjectCreated:*"]
    
    filter_suffix       = ".zip"
    filter_prefix       = "bronze/"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

# 3️⃣ Grant S3 Permission to Invoke Lambda
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scopusfunction.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.scopus_bucket.arn
}
