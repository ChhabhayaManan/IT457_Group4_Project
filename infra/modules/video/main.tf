# Optional video demo: one EC2 box that encodes a live HLS stream with FFmpeg.
# Off unless enable_video = true. Reached through Session Manager only.

data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

locals {
  scripts = { for f in fileset(var.video_dir, "*.sh") : f => filebase64("${var.video_dir}/${f}") }
  env     = {}
}

resource "aws_security_group" "video" {
  name        = "${var.name}-video"
  description = "Video ingest box: no inbound, all outbound"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.name}-video" }
}

resource "aws_iam_role" "video" {
  name = "${var.name}-video"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.video.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "video" {
  name = "${var.name}-video"
  role = aws_iam_role.video.name
}

resource "aws_instance" "video" {
  ami                    = data.aws_ssm_parameter.al2023_ami.value
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.video.id]
  iam_instance_profile   = aws_iam_instance_profile.video.name

  user_data = templatefile("${path.module}/user_data.sh", {
    ffmpeg_url = var.ffmpeg_url
    scripts    = local.scripts
    env        = local.env
  })
  user_data_replace_on_change = true

  credit_specification {
    cpu_credits = "unlimited"
  }

  metadata_options {
    http_tokens = "required"
  }

  tags = { Name = "${var.name}-video" }
}
