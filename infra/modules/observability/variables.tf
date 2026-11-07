variable "name" {
  description = "Dashboard name and alarm name prefix."
  type        = string
}

variable "aws_region" {
  type = string
}

variable "asg_name" {
  type = string
}

variable "alb_arn_suffix" {
  description = "LoadBalancer dimension for ALB metrics."
  type        = string
}

variable "target_group_arn_suffix" {
  description = "TargetGroup dimension for target health metrics."
  type        = string
}
