# One dashboard with everything an experiment needs on screen, plus two alarms
# whose state changes we screenshot during E2. The CPU alarms that drive scaling
# live with the scaling policy in the compute module.

locals {
  asg_dim = ["AWS/AutoScaling", "GroupInServiceInstances", "AutoScalingGroupName", var.asg_name]

  widgets = [
    {
      type   = "metric"
      x      = 0
      y      = 0
      width  = 12
      height = 6
      properties = {
        title  = "Instances (in service vs desired)"
        region = var.aws_region
        stat   = "Average"
        period = 60
        view   = "timeSeries"
        metrics = [
          local.asg_dim,
          ["AWS/AutoScaling", "GroupDesiredCapacity", "AutoScalingGroupName", var.asg_name],
        ]
      }
    },
    {
      type   = "metric"
      x      = 12
      y      = 0
      width  = 12
      height = 6
      properties = {
        title   = "Average CPU across the group (%)"
        region  = var.aws_region
        stat    = "Average"
        period  = 60
        view    = "timeSeries"
        metrics = [["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", var.asg_name]]
        annotations = {
          horizontal = [
            { label = "scale out", value = 50 },
            { label = "scale in", value = 20 },
          ]
        }
      }
    },
    {
      type   = "metric"
      x      = 0
      y      = 6
      width  = 12
      height = 6
      properties = {
        title  = "Load balancer response time (s)"
        region = var.aws_region
        period = 60
        view   = "timeSeries"
        metrics = [
          ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix, { stat = "p50", label = "p50" }],
          ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix, { stat = "p95", label = "p95" }],
        ]
      }
    },
    {
      type   = "metric"
      x      = 12
      y      = 6
      width  = 12
      height = 6
      properties = {
        title  = "Requests and errors per minute"
        region = var.aws_region
        stat   = "Sum"
        period = 60
        view   = "timeSeries"
        metrics = [
          ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", var.alb_arn_suffix],
          ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", var.alb_arn_suffix],
          ["AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count", "LoadBalancer", var.alb_arn_suffix],
        ]
      }
    },
    {
      type   = "metric"
      x      = 0
      y      = 12
      width  = 12
      height = 6
      properties = {
        title  = "Healthy targets"
        region = var.aws_region
        stat   = "Minimum"
        period = 60
        view   = "timeSeries"
        metrics = [
          ["AWS/ApplicationELB", "HealthyHostCount", "TargetGroup", var.target_group_arn_suffix, "LoadBalancer", var.alb_arn_suffix],
          ["AWS/ApplicationELB", "UnHealthyHostCount", "TargetGroup", var.target_group_arn_suffix, "LoadBalancer", var.alb_arn_suffix],
        ]
      }
    },
  ]
}

resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = var.name
  dashboard_body = jsonencode({ widgets = local.widgets })
}

resource "aws_cloudwatch_metric_alarm" "errors_5xx" {
  alarm_name          = "${var.name}-5xx"
  alarm_description   = "More than 10 server errors in a minute"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  dimensions          = { LoadBalancer = var.alb_arn_suffix }
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 1
  threshold           = 10
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "latency_p95" {
  alarm_name          = "${var.name}-p95-latency"
  alarm_description   = "p95 response time above 1 second"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "TargetResponseTime"
  dimensions          = { LoadBalancer = var.alb_arn_suffix }
  extended_statistic  = "p95"
  period              = 60
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
}
