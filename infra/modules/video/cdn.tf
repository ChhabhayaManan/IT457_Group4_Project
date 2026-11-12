# Segments go to a private S3 bucket and viewers fetch them through CloudFront,
# the same way a real OTT platform serves video: the origin is hit once per
# segment per edge, not once per viewer.
#   *.ts   segments never change     -> cached (Managed-CachingOptimized)
#   *.m3u8 live playlists change     -> cached 2 s only

data "aws_caller_identity" "current" {}

data "aws_cloudfront_cache_policy" "optimized" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_response_headers_policy" "cors" {
  name = "Managed-SimpleCORS" # lets the hls.js page load the stream from any origin
}

resource "aws_s3_bucket" "video" {
  bucket        = "${var.name}-video-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "video" {
  bucket = aws_s3_bucket.video.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "video" {
  bucket = aws_s3_bucket.video.id

  rule {
    id     = "expire-live-segments"
    status = "Enabled"
    filter {
      prefix = "live/"
    }
    expiration {
      days = 1
    }
  }
}

resource "aws_cloudfront_cache_policy" "playlist" {
  name        = "${var.name}-playlist-2s"
  comment     = "Live HLS playlists: cache for 2 seconds"
  min_ttl     = 0
  default_ttl = 2
  max_ttl     = 2

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }
    headers_config {
      header_behavior = "none"
    }
    query_strings_config {
      query_string_behavior = "none"
    }
  }
}

resource "aws_cloudfront_origin_access_control" "video" {
  name                              = "${var.name}-video"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "video" {
  enabled             = true
  comment             = "${var.name} video (HLS)"
  price_class         = "PriceClass_200"
  default_root_object = "index.html"

  origin {
    origin_id                = "video-bucket"
    domain_name              = aws_s3_bucket.video.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.video.id
  }

  default_cache_behavior {
    target_origin_id           = "video-bucket"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD", "OPTIONS"]
    cached_methods             = ["GET", "HEAD"]
    cache_policy_id            = data.aws_cloudfront_cache_policy.optimized.id
    response_headers_policy_id = data.aws_cloudfront_response_headers_policy.cors.id
  }

  ordered_cache_behavior {
    path_pattern               = "*.m3u8"
    target_origin_id           = "video-bucket"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD", "OPTIONS"]
    cached_methods             = ["GET", "HEAD"]
    cache_policy_id            = aws_cloudfront_cache_policy.playlist.id
    response_headers_policy_id = data.aws_cloudfront_response_headers_policy.cors.id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# Only this distribution may read the bucket.
resource "aws_s3_bucket_policy" "video" {
  bucket = aws_s3_bucket.video.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.video.arn}/*"
      Condition = { StringEquals = { "AWS:SourceArn" = aws_cloudfront_distribution.video.arn } }
    }]
  })
}

# The ingest box uploads segments and playlists.
resource "aws_iam_role_policy" "upload" {
  name = "video-upload"
  role = aws_iam_role.video.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.video.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"]
        Resource = "${aws_s3_bucket.video.arn}/*"
      },
    ]
  })
}
