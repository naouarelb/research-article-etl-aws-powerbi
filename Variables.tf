variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "eu-north-1"
}

variable "aws_iam_role" {
  description = "The AWS role to deploy resources"
  type        = string
  default     = "ScopusRole"
}

variable "aws_iam_policy" {
  description = "The AWS policy to attach to the role"
  type        = string
  default     = "ScopusPolicy"
}