# AWS Budget and cost monitoring for AtmosInsight
# Add this to your main Terraform configuration

resource "aws_budgets_budget" "atmosinsight" {
  name         = "atmosinsight-monthly-budget"
  budget_type  = "COST"
  limit_amount = var.budget_limit
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  
  cost_filters {
    tag {
      key = "Project"
      values = ["AtmosInsight"]
    }
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 90
    threshold_type            = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }

  depends_on = [aws_sns_topic.budget_alerts]
}

resource "aws_sns_topic" "budget_alerts" {
  name = "atmosinsight-budget-alerts"
  
  tags = var.tags
}

resource "aws_sns_topic_subscription" "budget_email" {
  topic_arn = aws_sns_topic.budget_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Alarms for critical issues
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "atmosinsight-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors Lambda function errors"
  alarm_actions       = [aws_sns_topic.budget_alerts.arn]

  dimensions = {
    FunctionName = "atmosinsight-healthz"
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx" {
  alarm_name          = "atmosinsight-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors API Gateway 5XX errors"
  alarm_actions       = [aws_sns_topic.budget_alerts.arn]

  tags = var.tags
}