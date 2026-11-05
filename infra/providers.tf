provider "aws" {
  region = var.aws_region

  # Every resource gets Project=group4-hotstar, so cost can be filtered by tag
  # and leftover resources are easy to find.
  default_tags {
    tags = {
      Project = var.project_name
    }
  }
}
