terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # O bucket é criado em infra/bootstrap (rode aquele primeiro)
  backend "s3" {
    bucket       = "levi-tfstate-ec2-deploy-20261120"
    key          = "ec2_deploy/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "ec2_deploy"
      ManagedBy = "terraform"
    }
  }
}
