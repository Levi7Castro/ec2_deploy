terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket       = "levi-tfstate-ec2-deploy-20261120"
    key          = "ec2_deploy/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "meu_bucket" {
  bucket = "levi-tfstate-ec2-deploy-20261120"   # troque por um nome só seu

  tags = {
    Name        = "My bucket"
    Environment = "Dev"
  }
}

# Versionamento: permite recuperar versões antigas do state
resource "aws_s3_bucket_versioning" "meu_bucket" {
  bucket = aws_s3_bucket.meu_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Bloqueia qualquer acesso público (state pode ter dados sensíveis)
resource "aws_s3_bucket_public_access_block" "meu_bucket" {
  bucket                  = aws_s3_bucket.meu_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

