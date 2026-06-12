output "app_url" {
  description = "Public URL of the APIs (EC2 public DNS)"
  value       = "http://${module.ec2.public_dns}"
}

output "ec2_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = module.ec2.public_ip
}

output "ec2_instance_id" {
  description = "Instance ID of the EC2 host (used for SSM deployments)"
  value       = module.ec2.instance_id
}

output "dashboard_url" {
  description = "CloudFront URL for the health dashboard"
  value       = module.frontend.dashboard_url
}

output "ecr_repository_urls" {
  description = "ECR repository URLs for each service"
  value       = module.ecr.repository_urls
}

output "s3_dashboard_bucket" {
  description = "S3 bucket name for dashboard files"
  value       = module.frontend.s3_bucket_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (needed for cache invalidation)"
  value       = module.frontend.cloudfront_distribution_id
}
