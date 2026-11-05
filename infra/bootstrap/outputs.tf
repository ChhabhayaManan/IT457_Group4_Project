output "state_bucket" {
  description = "Put this name in infra/backend.hcl."
  value       = aws_s3_bucket.state.bucket
}
