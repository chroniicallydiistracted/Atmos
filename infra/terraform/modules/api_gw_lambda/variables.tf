variable "static_bucket_name" {
  description = "Name of the S3 static assets bucket"
  type        = string
}

variable "derived_bucket_name" {
  description = "Name of the S3 derived data bucket"
  type        = string
}

variable "cloudfront_domain" {
  description = "CloudFront distribution domain for CORS"
  type        = string
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 1536
}

variable "api_throttle_rate" {
  description = "API Gateway throttle rate limit"
  type        = number
  default     = 5
}

variable "api_throttle_burst" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 10
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}