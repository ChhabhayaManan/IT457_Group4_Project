output "instance_id" {
  value = aws_instance.loadgen.id
}

output "results_bucket" {
  value = aws_s3_bucket.results.bucket
}
