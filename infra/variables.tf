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
