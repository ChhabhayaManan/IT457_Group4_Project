output "asg_name" {
  value = aws_autoscaling_group.app.name
}

output "instance_role_name" {
  value = aws_iam_role.app.name
}
