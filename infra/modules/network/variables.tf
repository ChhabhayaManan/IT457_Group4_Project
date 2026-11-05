variable "name" {
  description = "Name prefix for every resource."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC. Subnets are /24s carved from it."
  type        = string
}
