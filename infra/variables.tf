variable "region" {
  description = "Região da AWS"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "Tipo da instância EC2"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "Nome de um key pair existente na AWS para SSH (opcional)"
  type        = string
  default     = null
}

variable "ssh_cidr" {
  description = "CIDR liberado para SSH, ex: \"SEU.IP.PUBLICO/32\". Se null, a porta 22 fica fechada"
  type        = string
  default     = null
}

variable "repo_url" {
  description = "Repositório (público) que a EC2 clona para fazer o build"
  type        = string
  default     = "https://github.com/Levi7Castro/ec2_deploy.git"
}
