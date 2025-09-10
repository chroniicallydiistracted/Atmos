# API Gateway with Lambda functions

# IAM role for Lambda functions
resource "aws_iam_role" "lambda_role" {
  name = "atmosinsight-lambda-role"

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

  tags = var.tags
}

# Lambda policy for S3 and CloudWatch
resource "aws_iam_role_policy" "lambda_policy" {
  name = "atmosinsight-lambda-policy"
  role = aws_iam_role.lambda_role.id

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
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.static_bucket_name}/*",
          "arn:aws:s3:::${var.derived_bucket_name}/*",
          "arn:aws:s3:::${var.static_bucket_name}",
          "arn:aws:s3:::${var.derived_bucket_name}",
          "arn:aws:s3:::noaa-goes16/*",
          "arn:aws:s3:::noaa-nexrad-level2/*",
          "arn:aws:s3:::noaa-mrms-pds/*"
        ]
      }
    ]
  })
}

# Lambda functions
resource "aws_lambda_function" "healthz" {
  function_name = "atmosinsight-healthz"
  role          = aws_iam_role.lambda_role.arn
  
  package_type = "Zip"
  filename     = "${path.module}/../../services/healthz/healthz.zip"
  handler      = "handler.lambda_handler"
  runtime      = "python3.11"
  
  timeout     = var.lambda_timeout
  memory_size = 256

  environment {
    variables = {
      STATIC_BUCKET_NAME  = var.static_bucket_name
      DERIVED_BUCKET_NAME = var.derived_bucket_name
      VERSION            = "v0.1.0"
    }
  }

  tags = var.tags
}

# Placeholder for other Lambda functions (would be container images in production)
resource "aws_lambda_function" "tiler" {
  function_name = "atmosinsight-tiler"
  role          = aws_iam_role.lambda_role.arn
  
  package_type = "Zip"
  filename     = "${path.module}/../../services/healthz/healthz.zip"  # Placeholder
  handler      = "handler.lambda_handler"
  runtime      = "python3.11"
  
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory

  environment {
    variables = {
      DERIVED_BUCKET_NAME = var.derived_bucket_name
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "radar_prepare" {
  function_name = "atmosinsight-radar-prepare"
  role          = aws_iam_role.lambda_role.arn
  
  package_type = "Zip"
  filename     = "${path.module}/../../services/healthz/healthz.zip"  # Placeholder
  handler      = "handler.lambda_handler"
  runtime      = "python3.11"
  
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory

  environment {
    variables = {
      DERIVED_BUCKET_NAME = var.derived_bucket_name
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "goes_prepare" {
  function_name = "atmosinsight-goes-prepare"
  role          = aws_iam_role.lambda_role.arn
  
  package_type = "Zip"
  filename     = "${path.module}/../../services/healthz/healthz.zip"  # Placeholder
  handler      = "handler.lambda_handler"
  runtime      = "python3.11"
  
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory

  environment {
    variables = {
      DERIVED_BUCKET_NAME = var.derived_bucket_name
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "mrms_prepare" {
  function_name = "atmosinsight-mrms-prepare"
  role          = aws_iam_role.lambda_role.arn
  
  package_type = "Zip"
  filename     = "${path.module}/../../services/healthz/healthz.zip"  # Placeholder
  handler      = "handler.lambda_handler"
  runtime      = "python3.11"
  
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory

  environment {
    variables = {
      DERIVED_BUCKET_NAME = var.derived_bucket_name
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "alerts_bake" {
  function_name = "atmosinsight-alerts-bake"
  role          = aws_iam_role.lambda_role.arn
  
  package_type = "Zip"
  filename     = "${path.module}/../../services/healthz/healthz.zip"  # Placeholder
  handler      = "handler.lambda_handler"
  runtime      = "python3.11"
  
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory

  environment {
    variables = {
      DERIVED_BUCKET_NAME = var.derived_bucket_name
    }
  }

  tags = var.tags
}

# API Gateway HTTP API
resource "aws_apigatewayv2_api" "main" {
  name          = "atmosinsight-api"
  protocol_type = "HTTP"
  
  cors_configuration {
    allow_origins     = ["https://${var.cloudfront_domain}", "http://localhost:3000"]
    allow_headers     = ["content-type", "x-amz-date", "authorization", "x-api-key"]
    allow_methods     = ["*"]
    expose_headers    = ["date", "keep-alive"]
    max_age          = 86400
    allow_credentials = false
  }

  tags = var.tags
}

# Lambda integrations
resource "aws_apigatewayv2_integration" "healthz" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  
  integration_method = "POST"
  integration_uri    = aws_lambda_function.healthz.invoke_arn
}

resource "aws_apigatewayv2_integration" "tiler" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  
  integration_method = "POST"
  integration_uri    = aws_lambda_function.tiler.invoke_arn
}

resource "aws_apigatewayv2_integration" "radar_prepare" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  
  integration_method = "POST"
  integration_uri    = aws_lambda_function.radar_prepare.invoke_arn
}

resource "aws_apigatewayv2_integration" "goes_prepare" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  
  integration_method = "POST"
  integration_uri    = aws_lambda_function.goes_prepare.invoke_arn
}

resource "aws_apigatewayv2_integration" "mrms_prepare" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  
  integration_method = "POST"
  integration_uri    = aws_lambda_function.mrms_prepare.invoke_arn
}

resource "aws_apigatewayv2_integration" "alerts_bake" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  
  integration_method = "POST"
  integration_uri    = aws_lambda_function.alerts_bake.invoke_arn
}

# API Routes
resource "aws_apigatewayv2_route" "healthz" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /healthz"
  target    = "integrations/${aws_apigatewayv2_integration.healthz.id}"
}

resource "aws_apigatewayv2_route" "tiles" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /tiles/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.tiler.id}"
}

resource "aws_apigatewayv2_route" "radar_prepare" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /radar/prepare"
  target    = "integrations/${aws_apigatewayv2_integration.radar_prepare.id}"
}

resource "aws_apigatewayv2_route" "goes_prepare" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /goes/prepare"
  target    = "integrations/${aws_apigatewayv2_integration.goes_prepare.id}"
}

resource "aws_apigatewayv2_route" "mrms_prepare" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /mosaic/prepare"
  target    = "integrations/${aws_apigatewayv2_integration.mrms_prepare.id}"
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "healthz" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.healthz.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "tiler" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.tiler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "radar_prepare" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.radar_prepare.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "goes_prepare" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.goes_prepare.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "mrms_prepare" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.mrms_prepare.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# API Gateway stage
resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "v1"
  auto_deploy = true

  throttle_settings {
    rate_limit  = var.api_throttle_rate
    burst_limit = var.api_throttle_burst
  }

  tags = var.tags
}