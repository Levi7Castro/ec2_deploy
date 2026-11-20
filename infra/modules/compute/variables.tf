variable "vpc_id" {
  description = "VPC onde o security group é criado"
  type        = string
}

variable "subnet_id" {
  description = "Subnet (pública) onde a instância sobe"
  type        = string
}

variable "instance_type" {
  description = "Tipo da instância EC2"
  type        = string
}

variable "key_name" {
  description = "Nome de um key pair existente na AWS para SSH (opcional)"
  type        = string
  default     = null
}

variable "ssh_cidr" {
  description = "CIDR liberado para SSH. Se null, a porta 22 fica fechada"
  type        = string
  default     = null
}

variable "repo_url" {
  description = "Repositório (público) que a EC2 clona para fazer o build"
  type        = string
}
