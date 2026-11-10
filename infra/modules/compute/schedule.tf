# Predictive pre-warm (E3): the match start time is known, so raise the floor
# before the spike instead of waiting for CPU alarms. Step scaling stays on top.
#   prewarm_start: min = desired = prewarm_size (servers boot ahead of the spike)
#   prewarm_end:   min back to 1; the CPU-low alarm then removes servers slowly

resource "aws_autoscaling_schedule" "prewarm" {
  count = var.scaling_mode == "scheduled" ? 1 : 0

  scheduled_action_name  = "${var.name}-prewarm"
  autoscaling_group_name = aws_autoscaling_group.app.name
  start_time             = var.prewarm_start
  min_size               = var.prewarm_size
  max_size               = var.asg_max
  desired_capacity       = var.prewarm_size
}

resource "aws_autoscaling_schedule" "release" {
  count = var.scaling_mode == "scheduled" ? 1 : 0

  scheduled_action_name  = "${var.name}-prewarm-release"
  autoscaling_group_name = aws_autoscaling_group.app.name
  start_time             = var.prewarm_end
  min_size               = 1
  max_size               = var.asg_max
  desired_capacity       = -1 # -1 = leave desired alone
}
