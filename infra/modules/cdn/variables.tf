variable "name" {
  description = "Name prefix for every resource."
  type        = string
}

variable "alb_dns_name" {
  description = "The load balancer CloudFront forwards to."
  type        = string
}
