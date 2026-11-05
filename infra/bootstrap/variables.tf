variable "project_name" {
  description = "Prefix for the state bucket name and the Project tag."
  type        = string
  default     = "group4-hotstar"
}

variable "aws_region" {
  description = "Region for the state bucket."
  type        = string
  default     = "ap-south-1"
}
