output "instance_id" {
  description = "Ingest box, for aws ssm start-session."
  value       = aws_instance.video.id
}

output "bucket" {
  description = "Private bucket the segments are uploaded to."
  value       = aws_s3_bucket.video.bucket
}

output "stream_url" {
  description = "HLS master playlist through CloudFront."
  value       = "https://${aws_cloudfront_distribution.video.domain_name}/live/master.m3u8"
}

output "player_url" {
  description = "Player page, once video/player/index.html is uploaded to the bucket root."
  value       = "https://${aws_cloudfront_distribution.video.domain_name}/"
}
