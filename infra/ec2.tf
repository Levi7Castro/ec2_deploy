data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  owners = ["099720109477"] # Canonical
}

resource "aws_security_group" "allow_ssh_http" {
  name        = "streamlit-sg"
  description = "Streamlit (8501) e SSH opcional"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Streamlit"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH só é criado se ssh_cidr for informado
  dynamic "ingress" {
    for_each = var.ssh_cidr == null ? [] : [var.ssh_cidr]
    content {
      description = "SSH"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
    }
  }

  egress {
    description = "Saida liberada (apt, git clone, pip)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "streamlit-sg"
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.allow_ssh_http.id]
  key_name               = var.key_name

  # IMDSv2 obrigatório; hop limit 2 para o container conseguir ler o metadata
  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  # Recria a instância quando o script abaixo mudar
  user_data_replace_on_change = true

  user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail

    apt-get update
    apt-get install -y docker.io docker-buildx git
    systemctl enable --now docker

    # Clonar o repositório do GitHub (precisa ser público)
    git clone ${var.repo_url} /app

    # Construir e executar o contêiner Docker
    cd /app
    docker build -t streamlit-app .
    docker run -d --name streamlit --restart unless-stopped -p 8501:8501 streamlit-app
  EOF

  tags = {
    Name = "HelloStreamlit"
  }
}
