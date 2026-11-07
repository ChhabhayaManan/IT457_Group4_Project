output "domain_name" {
  value = aws_cloudfront_distribution.this.domain_name
}

output "distribution_id" {
  description = "Used as the DistributionId dimension in CloudWatch."
  value       = aws_cloudfront_distribution.this.id
}
