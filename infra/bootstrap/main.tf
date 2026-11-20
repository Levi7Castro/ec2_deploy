# Bucket S3 que guarda o state do Terraform de infra/.
# Rode UMA vez, antes de infra/. O state deste diretório fica local
# (terraform.tfstate, ignorado pelo git) — não apague.

terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "tfstate" {
  bucket = "levi-tfstate-ec2-deploy-20261120" # nome global: troque se for reutilizar

  tags = {
    Name      = "terraform-state"
    Project   = "ec2_deploy"
    ManagedBy = "terraform"
  }
}

# Versionamento: permite recuperar versões antigas do state
resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Bloqueia qualquer acesso público (state pode ter dados sensíveis)
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "bucket_name" {
  value = aws_s3_bucket.tfstate.bucket
}
