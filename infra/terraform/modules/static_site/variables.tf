variable "domain_name" {
  description = "Domain name for the application"
  type        = string
}

variable "create_route53_zone" {
  description = "Whether to create a Route53 hosted zone"
  type        = bool
  default     = true
}

variable "acm_certificate_arn" {
  description = "ARN of existing ACM certificate (optional)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}