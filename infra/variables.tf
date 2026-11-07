variable "project_name" {
  description = "Name prefix for resources and the value of the Project tag."
  type        = string
  default     = "group4-hotstar"
}

variable "aws_region" {
  description = "AWS region for every resource."
  type        = string
  default     = "ap-south-1"
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC."
  type        = string
  default     = "10.40.0.0/16"
}

variable "budget_email" {
  description = "Email that receives the $20 and $50 budget alerts. Set it in terraform.tfvars."
  type        = string
}

variable "instance_type" {
  description = "App server type. Keep the same for every run so results compare. c7i-flex.large is allowed on the AWS Free plan."
  type        = string
  default     = "c7i-flex.large"
}

variable "fixed_size" {
  description = "Instance count when the group has a fixed size (E1: 1, 2, 4, 8)."
  type        = number
  default     = 1

  validation {
    condition     = var.fixed_size >= 1 && var.fixed_size <= 10
    error_message = "fixed_size must be between 1 and 10."
  }
}

variable "enable_loadgen" {
  description = "Create the k6 load generator instance. Off for the base deployment."
  type        = bool
  default     = false
}

variable "loadgen_instance_type" {
  description = "k6 box type (Free plan allows c7i-flex.large, 2 vCPU). Check its CPU stays under 80% during runs."
  type        = string
  default     = "c7i-flex.large"
}

variable "play_iterations" {
  description = "PBKDF2 rounds per /play call: the CPU cost of one playback request."
  type        = number
  default     = 20000
}
