output "api_gateway_url" {
  description = "API Gateway base URL"
  value       = "https://${aws_apigatewayv2_api.main.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/v1"
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = aws_apigatewayv2_api.main.id
}

# Lambda function ARNs for EventBridge integration
output "healthz_function_arn" {
  value = aws_lambda_function.healthz.arn
}

output "tiler_function_arn" {
  value = aws_lambda_function.tiler.arn
}

output "radar_prepare_function_arn" {
  value = aws_lambda_function.radar_prepare.arn
}

output "goes_prepare_function_arn" {
  value = aws_lambda_function.goes_prepare.arn
}

output "mrms_prepare_function_arn" {
  value = aws_lambda_function.mrms_prepare.arn
}

output "alerts_bake_function_arn" {
  value = aws_lambda_function.alerts_bake.arn
}

data "aws_region" "current" {}