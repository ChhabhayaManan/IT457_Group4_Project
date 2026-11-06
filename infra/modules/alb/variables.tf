variable "name" {
  description = "Name prefix for every resource."
  type        = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  description = "Subnets the load balancer lives in (two AZs)."
  type        = list(string)
}

variable "app_port" {
  description = "Port the app listens on."
  type        = number
  default     = 8000
}
