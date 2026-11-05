terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Partial configuration: bucket, key and region come from backend.hcl
  # (copy backend.hcl.example). use_lockfile gives native S3 state locking,
  # so no DynamoDB table is needed.
  backend "s3" {
    use_lockfile = true
    encrypt      = true
  }
}
