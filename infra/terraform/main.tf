terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# Static site with S3, CloudFront, ACM, and Route53
module "static_site" {
  source                = "./modules/static_site"
  domain_name          = var.domain_name
  create_route53_zone  = var.create_route53_zone
  acm_certificate_arn  = var.acm_certificate_arn
  
  tags = var.tags
}

# API Gateway with Lambda functions
module "api" {
  source = "./modules/api_gw_lambda"
  
  # S3 buckets from static site module
  static_bucket_name  = module.static_site.static_bucket_name
  derived_bucket_name = module.static_site.derived_bucket_name
  
  # CloudFront distribution for CORS origins
  cloudfront_domain = module.static_site.cloudfront_domain
  
  tags = var.tags
}

# EventBridge schedules for automated data processing
module "events" {
  source = "./modules/events"
  
  # Lambda function ARNs from API module
  mrms_prepare_function_arn   = module.api.mrms_prepare_function_arn
  alerts_bake_function_arn    = module.api.alerts_bake_function_arn
  
  tags = var.tags
}

# Optional DynamoDB for indices and caching
module "dynamo" {
  count  = var.enable_dynamo ? 1 : 0
  source = "./modules/dynamo"
  
  tags = var.tags
}