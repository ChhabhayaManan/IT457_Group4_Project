# k6 load generator: one EC2 instance in the same region as the app, so our
# home network is never the bottleneck. Reached through Session Manager only.
# Test scripts and results go through an S3 bucket.

data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "results" {
  bucket        = "${var.name}-results-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "results" {
  bucket = aws_s3_bucket.results.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# loadtest/ (minus its tests) is uploaded on every apply; run.sh syncs it down before each run.
resource "aws_s3_object" "scripts" {
  for_each = toset([
    for f in fileset(var.loadtest_dir, "**/*.{js,sh,py}") : f if !startswith(f, "tests/")
  ])

  bucket = aws_s3_bucket.results.id
  key    = "scripts/${each.value}"
  source = "${var.loadtest_dir}/${each.value}"
  etag   = filemd5("${var.loadtest_dir}/${each.value}")
}

resource "aws_security_group" "loadgen" {
  name        = "${var.name}-loadgen"
  description = "k6 box: no inbound, all outbound"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.name}-loadgen" }
}

resource "aws_iam_role" "loadgen" {
  name = "${var.name}-loadgen"

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
  role       = aws_iam_role.loadgen.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "results" {
  name = "results-bucket"
  role = aws_iam_role.loadgen.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.results.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "${aws_s3_bucket.results.arn}/*"
      },
    ]
  })
}

resource "aws_iam_instance_profile" "loadgen" {
  name = "${var.name}-loadgen"
  role = aws_iam_role.loadgen.name
}

resource "aws_instance" "loadgen" {
  ami                    = data.aws_ssm_parameter.al2023_ami.value
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.loadgen.id]
  iam_instance_profile   = aws_iam_instance_profile.loadgen.name

  user_data = templatefile("${path.module}/user_data.sh", {
    k6_version     = var.k6_version
    results_bucket = aws_s3_bucket.results.bucket
  })
  # Boot script changes only take effect on a new instance.
  user_data_replace_on_change = true

  # Credit setting only exists on burstable (t*) types.
  dynamic "credit_specification" {
    for_each = startswith(var.instance_type, "t") ? [1] : []
    content {
      cpu_credits = "unlimited"
    }
  }

  monitoring = true

  metadata_options {
    http_tokens = "required"
  }

  tags = { Name = "${var.name}-loadgen" }
}
