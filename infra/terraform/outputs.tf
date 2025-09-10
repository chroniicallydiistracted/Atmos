output "cloudfront_domain" {
  description = "CloudFront distribution domain name"
  value       = module.static_site.cloudfront_domain
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.static_site.cloudfront_distribution_id
}

output "static_bucket_name" {
  description = "S3 static assets bucket name"
  value       = module.static_site.static_bucket_name
}

output "derived_bucket_name" {
  description = "S3 derived data bucket name"
  value       = module.static_site.derived_bucket_name
}

output "api_gateway_url" {
  description = "API Gateway base URL"
  value       = module.api.api_gateway_url
}

output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = module.static_site.route53_zone_id
}

output "route53_name_servers" {
  description = "Route53 hosted zone name servers"
  value       = module.static_site.route53_name_servers
}

output "acm_certificate_arn" {
  description = "ACM certificate ARN"
  value       = module.static_site.acm_certificate_arn
}

# Lambda function ARNs for monitoring and troubleshooting
output "lambda_functions" {
  description = "Lambda function ARNs"
  value = {
    healthz        = module.api.healthz_function_arn
    tiler          = module.api.tiler_function_arn
    radar_prepare  = module.api.radar_prepare_function_arn
    goes_prepare   = module.api.goes_prepare_function_arn
    mrms_prepare   = module.api.mrms_prepare_function_arn
    alerts_bake    = module.api.alerts_bake_function_arn
  }
}