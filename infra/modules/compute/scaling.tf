# Reactive scaling (E2), the course rule: "if CPU goes above 50%, add another instance".
#   +1 instance when the group's average CPU is above 50% for 1 minute
#   -1 instance when it is below 20% for 5 minutes
# While an alarm stays in ALARM, Auto Scaling re-runs its policy every minute,
# so a long spike adds one server per minute (after each one's warm-up).

resource "aws_autoscaling_policy" "scale_out" {
  count = local.fixed ? 0 : 1

  name                      = "${var.name}-cpu-scale-out"
  autoscaling_group_name    = aws_autoscaling_group.app.name
  policy_type               = "StepScaling"
  adjustment_type           = "ChangeInCapacity"
  metric_aggregation_type   = "Average"
  estimated_instance_warmup = 60

  step_adjustment {
    scaling_adjustment          = 1
    metric_interval_lower_bound = 0
  }
}

resource "aws_autoscaling_policy" "scale_in" {
  count = local.fixed ? 0 : 1

  name                    = "${var.name}-cpu-scale-in"
  autoscaling_group_name  = aws_autoscaling_group.app.name
  policy_type             = "StepScaling"
  adjustment_type         = "ChangeInCapacity"
  metric_aggregation_type = "Average"

  step_adjustment {
    scaling_adjustment          = -1
    metric_interval_upper_bound = 0
  }
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  count = local.fixed ? 0 : 1

  alarm_name          = "${var.name}-cpu-high"
  alarm_description   = "Average CPU > 50% for 1 minute: add an instance"
  namespace           = "AWS/EC2"
  metric_name         = "CPUUtilization"
  dimensions          = { AutoScalingGroupName = aws_autoscaling_group.app.name }
  statistic           = "Average"
  period              = 60
  evaluation_periods  = 1
  threshold           = 50
  comparison_operator = "GreaterThanThreshold"
  alarm_actions       = [aws_autoscaling_policy.scale_out[0].arn]
}

resource "aws_cloudwatch_metric_alarm" "cpu_low" {
  count = local.fixed ? 0 : 1

  alarm_name          = "${var.name}-cpu-low"
  alarm_description   = "Average CPU < 20% for 5 minutes: remove an instance"
  namespace           = "AWS/EC2"
  metric_name         = "CPUUtilization"
  dimensions          = { AutoScalingGroupName = aws_autoscaling_group.app.name }
  statistic           = "Average"
  period              = 60
  evaluation_periods  = 5
  threshold           = 20
  comparison_operator = "LessThanThreshold"
  alarm_actions       = [aws_autoscaling_policy.scale_in[0].arn]
}
