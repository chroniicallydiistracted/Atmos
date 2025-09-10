# Static site hosting with S3 + CloudFront + ACM + Route53

# S3 bucket for static assets (SPA, PMTiles, styles, sprites, fonts)
resource "aws_s3_bucket" "static" {
  bucket        = "atmosinsight-static-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = var.tags
}

resource "aws_s3_bucket" "derived" {
  bucket        = "atmosinsight-derived-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = var.tags
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 bucket configurations
resource "aws_s3_bucket_public_access_block" "static" {
  bucket = aws_s3_bucket.static.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "derived" {
  bucket = aws_s3_bucket.derived.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle configuration for derived data (7 days retention)
resource "aws_s3_bucket_lifecycle_configuration" "derived" {
  bucket = aws_s3_bucket.derived.id

  rule {
    id     = "expire_derived_data"
    status = "Enabled"

    expiration {
      days = 7
    }

    noncurrent_version_expiration {
      noncurrent_days = 1
    }
  }
}

# CORS configuration for static bucket
resource "aws_s3_bucket_cors_configuration" "static" {
  bucket = aws_s3_bucket.static.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Route53 hosted zone for subdomain delegation
resource "aws_route53_zone" "main" {
  count = var.create_route53_zone ? 1 : 0
  name  = var.domain_name
  
  tags = var.tags
}

# ACM certificate for HTTPS
resource "aws_acm_certificate" "main" {
  count           = var.acm_certificate_arn == null ? 1 : 0
  domain_name     = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = [
    "*.${var.domain_name}"
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = var.tags
}

# DNS validation for ACM certificate
resource "aws_route53_record" "cert_validation" {
  for_each = var.create_route53_zone && var.acm_certificate_arn == null ? {
    for dvo in aws_acm_certificate.main[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.main[0].zone_id
}

resource "aws_acm_certificate_validation" "main" {
  count           = var.create_route53_zone && var.acm_certificate_arn == null ? 1 : 0
  certificate_arn = aws_acm_certificate.main[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# CloudFront Origin Access Control
resource "aws_cloudfront_origin_access_control" "static" {
  name                              = "atmosinsight-static-oac"
  description                       = "OAC for AtmosInsight static bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront distribution
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  aliases             = [var.domain_name]

  # S3 static origin
  origin {
    domain_name              = aws_s3_bucket.static.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.static.id
    origin_id                = "S3-static"
  }

  # API Gateway origin (will be added by api module)
  origin {
    domain_name = "api.placeholder.local"  # Will be updated by API module
    origin_id   = "API-Gateway"
    
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Default behavior for SPA
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-static"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  # PMTiles behavior (forward Range header)
  ordered_cache_behavior {
    path_pattern     = "/basemaps/*"
    target_origin_id = "S3-static"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    compress         = false
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      headers      = ["Range"]
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  # Static assets (styles, sprites, fonts)
  ordered_cache_behavior {
    path_pattern     = "/styles/*"
    target_origin_id = "S3-static"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    compress         = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 86400
    max_ttl     = 31536000
  }

  ordered_cache_behavior {
    path_pattern     = "/sprites/*"
    target_origin_id = "S3-static"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    compress         = false
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 86400
    max_ttl     = 31536000
  }

  ordered_cache_behavior {
    path_pattern     = "/fonts/*"
    target_origin_id = "S3-static"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    compress         = false
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 86400
    max_ttl     = 31536000
  }

  # API behaviors (will be configured by API module)
  ordered_cache_behavior {
    path_pattern     = "/tiles/*"
    target_origin_id = "API-Gateway"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    compress         = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  ordered_cache_behavior {
    path_pattern     = "/healthz"
    target_origin_id = "API-Gateway"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    compress         = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      cookies {
        forward = "none"
      }
    }

    # No caching for health endpoint
    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn != null ? var.acm_certificate_arn : aws_acm_certificate.main[0].arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = var.tags
}

# S3 bucket policy for CloudFront OAC
resource "aws_s3_bucket_policy" "static" {
  bucket = aws_s3_bucket.static.id
  policy = jsonencode({
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.static.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.main.arn
          }
        }
      }
    ]
  })
}

# Route53 alias record
resource "aws_route53_record" "main" {
  count   = var.create_route53_zone ? 1 : 0
  zone_id = aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }
}