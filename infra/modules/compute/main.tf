# App servers: a launch template (how to build one server) and an Auto Scaling
# Group (how many to run, in which subnets, behind which target group).

data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

locals {
  # Every .py file in app/ plus requirements.txt is copied into user data,
  # so a new app file is picked up without changing this module.
  app_file_names = setunion(fileset(var.app_dir, "*.py"), ["requirements.txt"])

  user_data = templatefile("${var.app_dir}/user_data.sh.tftpl", {
    app_files = { for f in local.app_file_names : f => filebase64("${var.app_dir}/${f}") }
    app_env   = var.app_env
  })
}

resource "aws_security_group" "app" {
  name        = "${var.name}-app"
  description = "App servers: port ${var.app_port} from the load balancer only"
  vpc_id      = var.vpc_id

  ingress {
    description     = "App port from the ALB"
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [var.alb_security_group_id]
  }

  egress {
    description = "Package installs through the NAT gateway"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.name}-app" }
}

resource "aws_launch_template" "app" {
  name_prefix   = "${var.name}-app-"
  image_id      = data.aws_ssm_parameter.al2023_ami.value
  instance_type = var.instance_type
  user_data     = base64encode(local.user_data)

  vpc_security_group_ids = [aws_security_group.app.id]

  iam_instance_profile {
    name = aws_iam_instance_profile.app.name
  }

  # Only burstable types (t3, t4g) take a credit setting. Unlimited means CPU
  # credits never run out mid-test and skew latency. c7i has a fixed full-speed CPU.
  dynamic "credit_specification" {
    for_each = startswith(var.instance_type, "t") ? [1] : []
    content {
      cpu_credits = "unlimited"
    }
  }

  # 1-minute CloudWatch metrics, so the scaling alarms react within a minute.
  monitoring {
    enabled = true
  }

  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  tag_specifications {
    resource_type = "instance"
    tags          = { Name = "${var.name}-app" }
  }

  lifecycle {
    precondition {
      condition     = length(local.user_data) < 16384
      error_message = "User data is over the 16 KB EC2 limit; keep app files small."
    }
  }
}

resource "aws_autoscaling_group" "app" {
  name                = "${var.name}-app"
  vpc_zone_identifier = var.private_subnet_ids
  target_group_arns   = [var.target_group_arn]

  min_size         = var.fixed_size
  max_size         = var.fixed_size
  desired_capacity = var.fixed_size

  health_check_type         = "ELB"
  health_check_grace_period = 120
  default_instance_warmup   = 60

  launch_template {
    id      = aws_launch_template.app.id
    version = aws_launch_template.app.latest_version
  }

  # Per-minute group metrics: the in-service instance graph in the console.
  enabled_metrics = [
    "GroupDesiredCapacity",
    "GroupInServiceInstances",
    "GroupPendingInstances",
    "GroupTerminatingInstances",
    "GroupTotalInstances",
  ]

  # A new launch template version (e.g. app change) replaces instances gradually.
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
    }
  }

  tag {
    key                 = "Name"
    value               = "${var.name}-app"
    propagate_at_launch = true
  }
}
