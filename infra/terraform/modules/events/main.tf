# EventBridge schedules for automated data processing

# EventBridge rule for MRMS processing (every 5 minutes)
resource "aws_cloudwatch_event_rule" "mrms_schedule" {
  name                = "atmosinsight-mrms-schedule"
  description         = "Trigger MRMS preparation every 5 minutes"
  schedule_expression = "rate(5 minutes)"

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "mrms_lambda" {
  rule      = aws_cloudwatch_event_rule.mrms_schedule.name
  target_id = "MRMSLambdaTarget"
  arn       = var.mrms_prepare_function_arn

  input = jsonencode({
    product = "reflq"
    time    = "latest"
  })
}

resource "aws_lambda_permission" "allow_eventbridge_mrms" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.mrms_prepare_function_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.mrms_schedule.arn
}

# EventBridge rule for NWS Alerts (every 5 minutes)
resource "aws_cloudwatch_event_rule" "alerts_schedule" {
  name                = "atmosinsight-alerts-schedule"
  description         = "Trigger alerts baking every 5 minutes"
  schedule_expression = "rate(5 minutes)"

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "alerts_lambda" {
  rule      = aws_cloudwatch_event_rule.alerts_schedule.name
  target_id = "AlertsLambdaTarget"
  arn       = var.alerts_bake_function_arn
}

resource "aws_lambda_permission" "allow_eventbridge_alerts" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.alerts_bake_function_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.alerts_schedule.arn
}