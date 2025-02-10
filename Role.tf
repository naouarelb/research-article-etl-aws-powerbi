# Create the IAM role
resource "aws_iam_role" "scopus_transformation_role" {
  name = var.aws_iam_role

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "glue.amazonaws.com", 
            "lambda.amazonaws.com"
          ]
        }
      }
    ]
  })
}

# Create Custom Policy for S3, Glue, and CloudWatch Logs
resource "aws_iam_policy" "scopus_policy_allow" {
  name        = "${var.aws_iam_policy}-allow"
  description = "Custom policy to allow S3, Glue, and CloudWatch Logs actions"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:*",
          "glue:*",
          "logs:*",
          "lambda:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "scopus_policy_allow_services" {
  name        = "${var.aws_iam_policy}-all-services"
  description = "Custom policy to deny insecure access to S3"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:*",
          "s3-object-lambda:*"
        ]
        Resource = "*"
      },
      {
        Sid       = "BaseAppPermissions"
        Effect    = "Allow"
        Action    = [
          "glue:*",
          "redshift:DescribeClusters",
          "redshift:DescribeClusterSubnetGroups",
          "iam:ListRoles",
          "iam:ListUsers",
          "iam:ListGroups",
          "iam:ListRolePolicies",
          "iam:GetRole",
          "iam:GetRolePolicy",
          "iam:ListAttachedRolePolicies",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeSubnets",
          "ec2:DescribeVpcs",
          "ec2:DescribeVpcEndpoints",
          "ec2:DescribeRouteTables",
          "ec2:DescribeVpcAttribute",
          "ec2:DescribeKeyPairs",
          "ec2:DescribeInstances",
          "ec2:DescribeImages",
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters",
          "rds:DescribeDBSubnetGroups",
          "s3:ListAllMyBuckets",
          "s3:ListBucket",
          "s3:GetBucketAcl",
          "s3:GetBucketLocation",
          "cloudformation:ListStacks",
          "cloudformation:DescribeStacks",
          "cloudformation:GetTemplateSummary",
          "dynamodb:ListTables",
          "kms:ListAliases",
          "kms:DescribeKey",
          "cloudwatch:GetMetricData",
          "cloudwatch:ListDashboards",
          "databrew:ListRecipes",
          "databrew:ListRecipeVersions",
          "databrew:DescribeRecipe"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "arn:aws:s3:::aws-glue-*/*",
          "arn:aws:s3:::*/*aws-glue-*/*",
          "arn:aws:s3:::aws-glue-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "tag:GetResources"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:CreateBucket"
        ]
        Resource = [
          "arn:aws:s3:::aws-glue-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:GetLogEvents"
        ]
        Resource = [
          "arn:aws:logs:*:*:/aws-glue/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudformation:CreateStack",
          "cloudformation:DeleteStack"
        ]
        Resource = "arn:aws:cloudformation:*:*:stack/aws-glue*/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:RunInstances"
        ]
        Resource = [
          "arn:aws:ec2:*:*:instance/*",
          "arn:aws:ec2:*:*:key-pair/*",
          "arn:aws:ec2:*:*:image/*",
          "arn:aws:ec2:*:*:security-group/*",
          "arn:aws:ec2:*:*:network-interface/*",
          "arn:aws:ec2:*:*:subnet/*",
          "arn:aws:ec2:*:*:volume/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:TerminateInstances",
          "ec2:CreateTags",
          "ec2:DeleteTags"
        ]
        Resource = [
          "arn:aws:ec2:*:*:instance/*"
        ]
        Condition = {
          StringLike = {
            "ec2:ResourceTag/aws:cloudformation:stack-id" = "arn:aws:cloudformation:*:*:stack/aws-glue-*/*"
          }
          StringEquals = {
            "ec2:ResourceTag/aws:cloudformation:logical-id" = "ZeppelinInstance"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = "arn:aws:iam::*:role/AWSGlueServiceRole*"
        Condition = {
          StringLike = {
            "iam:PassedToService" = [
              "glue.amazonaws.com"
            ]
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = "arn:aws:iam::*:role/AWSGlueServiceNotebookRole*"
        Condition = {
          StringLike = {
            "iam:PassedToService" = [
              "ec2.amazonaws.com"
            ]
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          "arn:aws:iam::*:role/service-role/AWSGlueServiceRole*"
        ]
        Condition = {
          StringLike = {
            "iam:PassedToService" = [
              "glue.amazonaws.com"
            ]
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "autoscaling:Describe*",
          "cloudwatch:*",
          "logs:*",
          "sns:*",
          "iam:GetPolicy",
          "iam:GetPolicyVersion",
          "iam:GetRole",
          "oam:ListSinks"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = "iam:CreateServiceLinkedRole"
        Resource = "arn:aws:iam::*:role/aws-service-role/events.amazonaws.com/AWSServiceRoleForCloudWatchEvents*"
        Condition = {
          StringLike = {
            "iam:AWSServiceName" = "events.amazonaws.com"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "oam:ListAttachedLinks"
        ]
        Resource = "arn:aws:oam:*:*:sink/*"
      }
    ]
  })
}


# Attach Custom Policy to the Role
resource "aws_iam_role_policy_attachment" "scopus_transformation_policy_attachment" {
  role       = aws_iam_role.scopus_transformation_role.name
  policy_arn = aws_iam_policy.scopus_policy_allow_services.arn
}
