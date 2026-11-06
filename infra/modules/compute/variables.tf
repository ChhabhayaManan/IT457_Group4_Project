variable "name" {
  description = "Name prefix for every resource."
  type        = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  description = "Subnets the app servers run in (two AZs)."
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Only this security group may reach the app port."
  type        = string
}

variable "target_group_arn" {
  description = "Target group the ASG registers instances with."
  type        = string
}

variable "instance_type" {
  type = string
}

variable "fixed_size" {
  description = "Number of instances when the group has a fixed size."
  type        = number
}

variable "app_dir" {
  description = "Path to the app/ folder whose files go into user data."
  type        = string
}

variable "app_env" {
  description = "Environment variables written to /etc/hotstar.env on each server."
  type        = map(string)
  default     = {}
}

variable "app_port" {
  type    = number
  default = 8000
}
