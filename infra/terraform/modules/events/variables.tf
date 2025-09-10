variable "mrms_prepare_function_arn" {
  description = "ARN of the MRMS preparation Lambda function"
  type        = string
}

variable "alerts_bake_function_arn" {
  description = "ARN of the alerts baking Lambda function"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}