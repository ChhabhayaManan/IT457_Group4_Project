output "instance_id" {
  description = "Ingest box, for aws ssm start-session."
  value       = aws_instance.video.id
}
