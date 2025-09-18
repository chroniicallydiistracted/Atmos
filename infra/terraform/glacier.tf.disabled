# S3 Glacier archiving for cost-effective historical data storage

# Lifecycle policy for derived data bucket - archive to Glacier after 90 days
resource "aws_s3_bucket_lifecycle_configuration" "derived_data_lifecycle" {
  bucket = module.static_site.derived_bucket_name

  rule {
    id     = "glacier_archival"
    status = "Enabled"

    # Apply to all weather data objects
    filter {
      prefix = "weather/"
    }

    # Standard IA after 30 days for recent access patterns
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Glacier Flexible Retrieval after 90 days (cost optimized)
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Deep Archive after 365 days (long-term preservation)
    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    # Delete incomplete multipart uploads after 7 days
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

    # Optional: Delete very old data after 7 years
    expiration {
      days = 2555  # ~7 years
    }
  }

  rule {
    id     = "temp_data_cleanup"
    status = "Enabled"

    # Clean up temporary processing files quickly
    filter {
      prefix = "tmp/"
    }

    expiration {
      days = 1
    }
  }

  rule {
    id     = "log_archival"
    status = "Enabled"

    # Archive logs more aggressively
    filter {
      prefix = "logs/"
    }

    transition {
      days          = 7
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    expiration {
      days = 730  # 2 years
    }
  }
}

# CloudWatch Log Group retention for Lambda functions
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = {
    healthz        = "/aws/lambda/atmosinsight-healthz"
    tiler          = "/aws/lambda/atmosinsight-tiler"
    radar_prepare  = "/aws/lambda/atmosinsight-radar-prepare"
    goes_prepare   = "/aws/lambda/atmosinsight-goes-prepare"
    mrms_prepare   = "/aws/lambda/atmosinsight-mrms-prepare"
    alerts_bake    = "/aws/lambda/atmosinsight-alerts-bake"
  }

  name              = each.value
  retention_in_days = 14  # Cost optimization - keep logs for 2 weeks
}

# S3 bucket for archival metadata and retrieval tracking
resource "aws_s3_bucket" "glacier_metadata" {
  bucket = "atmosinsight-glacier-metadata"
}

resource "aws_s3_bucket_versioning" "glacier_metadata" {
  bucket = aws_s3_bucket.glacier_metadata.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "glacier_metadata" {
  bucket = aws_s3_bucket.glacier_metadata.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lambda function for Glacier retrieval automation
resource "aws_lambda_function" "glacier_retrieval" {
  filename         = "glacier_retrieval.zip"
  function_name    = "atmosinsight-glacier-retrieval"
  role            = aws_iam_role.glacier_retrieval_role.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30

  environment {
    variables = {
      METADATA_BUCKET = aws_s3_bucket.glacier_metadata.id
      DERIVED_BUCKET  = module.static_site.derived_bucket_name
    }
  }
}

# IAM role for Glacier retrieval Lambda
resource "aws_iam_role" "glacier_retrieval_role" {
  name = "atmosinsight-glacier-retrieval"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "glacier_retrieval_policy" {
  name = "glacier-retrieval-policy"
  role = aws_iam_role.glacier_retrieval_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:RestoreObject",
          "s3:HeadObject"
        ]
        Resource = [
          "${module.static_site.derived_bucket_arn}/*",
          "${aws_s3_bucket.glacier_metadata.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          module.static_site.derived_bucket_arn,
          aws_s3_bucket.glacier_metadata.arn
        ]
      }
    ]
  })
}