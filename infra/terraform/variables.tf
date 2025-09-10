variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Domain name for the application (e.g., weather.westfam.media)"
  type        = string
}

variable "create_route53_zone" {
  description = "Whether to create a Route53 hosted zone for the domain"
  type        = bool
  default     = true
}

variable "acm_certificate_arn" {
  description = "ARN of existing ACM certificate (optional - will create one if not provided)"
  type        = string
  default     = null
}

variable "enable_dynamo" {
  description = "Whether to create DynamoDB tables for indices and caching"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "AtmosInsight"
    Environment = "production"
    Terraform   = "true"
  }
}

# Lambda configuration
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

# Rate limiting
variable "api_throttle_burst" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 10
}

variable "api_throttle_rate" {
  description = "API Gateway throttle rate limit"
  type        = number
  default     = 5
}

# Budget alerts
variable "budget_limit" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 30
}

# Alerting configuration
variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = "andre@westfam.media"
}

variable "discord_webhook_url" {
  description = "Discord webhook URL for notifications (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "twilio_account_sid" {
  description = "Twilio Account SID for SMS notifications (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "twilio_auth_token" {
  description = "Twilio Auth Token for SMS notifications (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "twilio_from_phone" {
  description = "Twilio phone number to send SMS from (optional)"
  type        = string
  default     = ""
}

variable "alert_phone" {
  description = "Phone number to send SMS alerts to (optional)"
  type        = string
  default     = ""
}