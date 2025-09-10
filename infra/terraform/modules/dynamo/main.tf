# Optional DynamoDB tables for indices and caching
# Can be used instead of S3-only indices for better performance

resource "aws_dynamodb_table" "indices" {
  name           = "atmosinsight-indices"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "layer_id"
  range_key      = "timestamp"

  attribute {
    name = "layer_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  # TTL for automatic cleanup of old entries
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "cache" {
  name           = "atmosinsight-cache"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "cache_key"

  attribute {
    name = "cache_key"
    type = "S"
  }

  # TTL for automatic cache expiration
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = var.tags
}