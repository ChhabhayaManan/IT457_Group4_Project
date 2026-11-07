variable "name" {
  description = "Name prefix for every resource."
  type        = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_id" {
  description = "Private subnet for the k6 box (outbound through the NAT)."
  type        = string
}

variable "instance_type" {
  type = string
}

variable "loadtest_dir" {
  description = "Path to loadtest/; its .js, .sh and .py files are uploaded to S3."
  type        = string
}

variable "k6_version" {
  type    = string
  default = "2.2.0"
}
