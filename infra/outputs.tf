output "vpc_id" {
  value = module.network.vpc_id
}

output "alb_url" {
  description = "Live URL of the load balancer (course deliverable 1)."
  value       = "http://${module.alb.alb_dns_name}"
}

output "asg_name" {
  value = module.compute.asg_name
}

output "dashboard_url" {
  value = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards/dashboard/${module.observability.dashboard_name}"
}

output "cdn_url" {
  value = try("http://${module.cdn[0].domain_name}", null)
}

output "loadgen_instance_id" {
  value = try(module.loadgen[0].instance_id, null)
}

output "results_bucket" {
  value = try(module.loadgen[0].results_bucket, null)
}
