output "static_bucket_name" {
  description = "Name of the S3 static assets bucket"
  value       = aws_s3_bucket.static.id
}

output "static_bucket_arn" {
  description = "ARN of the S3 static assets bucket"
  value       = aws_s3_bucket.static.arn
}

output "derived_bucket_name" {
  description = "Name of the S3 derived data bucket"
  value       = aws_s3_bucket.derived.id
}

output "derived_bucket_arn" {
  description = "ARN of the S3 derived data bucket"
  value       = aws_s3_bucket.derived.arn
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "cloudfront_arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.main.arn
}

output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = var.create_route53_zone ? aws_route53_zone.main[0].zone_id : null
}

output "route53_name_servers" {
  description = "Route53 hosted zone name servers"
  value       = var.create_route53_zone ? aws_route53_zone.main[0].name_servers : null
}

output "acm_certificate_arn" {
  description = "ACM certificate ARN"
  value       = var.acm_certificate_arn != null ? var.acm_certificate_arn : aws_acm_certificate.main[0].arn
}