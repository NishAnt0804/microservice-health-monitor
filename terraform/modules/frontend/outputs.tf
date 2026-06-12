output "s3_bucket_name" {
  description = "Name of the S3 dashboard bucket"
  value       = aws_s3_bucket.dashboard.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 dashboard bucket"
  value       = aws_s3_bucket.dashboard.arn
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.dashboard.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.dashboard.domain_name
}

output "dashboard_url" {
  description = "URL of the health dashboard"
  value       = "https://${aws_cloudfront_distribution.dashboard.domain_name}"
}
