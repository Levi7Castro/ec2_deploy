# ec2_deploy

App de exemplo em **Streamlit** empacotado com **Docker** e publicado numa **EC2 da AWS** com **Terraform**.

O app tem três abas:

- **📊 Dashboard**: vendas de uma lanchonete fictícia, com filtros, métricas e gráficos
- **🎲 Laboratório**: simulador de investimento (Monte Carlo)
- **🖥️ Servidor**: mostra se está rodando numa EC2 (instance ID, tipo, AZ, IP)

## Arquitetura

```
 GitHub (repo público)
        │  git clone
        ▼
┌──────────────────────── VPC 10.0.0.0/16 ────────────────────────┐
│  Subnet pública 10.0.1.0/24                                      │
│  ┌──────────────── EC2 (Ubuntu 24.04, t3.micro) ──────────────┐  │
│  │  user_data: instala Docker → clona repo → build → run      │  │
│  │  ┌─────────────── container ───────────────┐               │  │
│  │  │  streamlit run app/app.py  :8501        │               │  │
│  │  └─────────────────────────────────────────┘               │  │
│  └────────────────────────────────────────────────────────────┘  │
│  Security group: 8501 aberta · 22 só se ssh_cidr for definido     │
└──────────────── Internet Gateway ────────────────────────────────┘
        ▲
   navegador → http://<ip-publico>:8501

State do Terraform → bucket S3 (versionado, privado, com lockfile)
```

## Estrutura

```
.
├── app/
│   └── app.py              # app Streamlit
├── infra/
│   ├── bootstrap/
│   │   └── main.tf         # bucket S3 do state (rodar uma vez)
│   ├── main.tf             # provider + backend S3
│   ├── variables.tf        # variáveis (região, tipo, SSH, repo)
│   ├── vpc.tf              # VPC, subnet, internet gateway, rotas
│   ├── ec2.tf              # AMI, security group, instância
│   └── outputs.tf          # IP e URL do app
├── Dockerfile
├── .dockerignore
├── pyproject.toml          # dependências (gerenciadas com uv)
└── uv.lock
```

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/) e Python 3.12
- [Docker](https://docs.docker.com/get-docker/)
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.10
- [AWS CLI](https://aws.amazon.com/cli/) configurado (`aws configure`)

## Rodar localmente

Com uv:

```bash
uv sync
uv run streamlit run app/app.py
```

Com Docker:

```bash
docker build -t ec2-deploy-streamlit .
docker run --rm -p 8501:8501 ec2-deploy-streamlit
```

Depois é só abrir http://localhost:8501.

## Deploy na AWS

### 1. Bucket do state (só na primeira vez)

```bash
cd infra/bootstrap
terraform init
terraform apply
```

> O state deste diretório fica **local** (`infra/bootstrap/terraform.tfstate`, fora do git). Não apague esse arquivo.
> O nome do bucket é global na AWS: se for usar em outra conta, troque o nome em `bootstrap/main.tf` **e** no `backend` de `infra/main.tf`.

### 2. Infraestrutura e app

A EC2 clona este repositório pelo `git clone`, então ele precisa estar **público** e com as mudanças enviadas (`git push`).

```bash
cd infra
terraform init
terraform apply
```

Ao terminar, o Terraform mostra a URL:

```
app_url = "http://34.x.x.x:8501"
```

O build dentro da EC2 leva **~2–5 min** depois do `apply`.

### Variáveis

| Variável        | Padrão                                        | Descrição                                   |
|-----------------|-----------------------------------------------|---------------------------------------------|
| `region`        | `us-east-1`                                   | Região da AWS                               |
| `instance_type` | `t3.micro`                                    | Tipo da instância                           |
| `key_name`      | `null`                                        | Key pair para SSH (opcional)                |
| `ssh_cidr`      | `null`                                        | Seu IP para SSH, ex. `1.2.3.4/32` (opcional) |
| `repo_url`      | `https://github.com/Levi7Castro/ec2_deploy.git` | Repositório que a EC2 clona               |

Exemplo com SSH:

```bash
terraform apply -var 'key_name=minha-chave' -var 'ssh_cidr=1.2.3.4/32'
```

### Atualizar o app

A EC2 só clona o repositório quando é criada. Para publicar uma nova versão:

```bash
git push
cd infra
terraform apply -replace=aws_instance.web
```

> O IP público muda a cada recriação.

## Destruir (para não pagar)

```bash
cd infra
terraform destroy
```

Isso remove a EC2, o security group e a VPC. O **bucket do state continua**, porque fica em `infra/bootstrap`. Ele custa centavos e permite subir tudo de novo com `terraform apply`.

Para conferir que não sobrou nada:

```bash
aws ec2 describe-instances --region us-east-1 \
  --query "Reservations[].Instances[].[InstanceId,State.Name]" --output table
```

> 💡 Crie um alerta **Zero spend budget** em *Billing → Budgets* para ser avisado de qualquer cobrança.

## Troubleshooting

| Problema | O que verificar |
|---|---|
| App não abre depois do `apply` | Espere alguns minutos. O build roda no boot. |
| Ainda não abre | Log do boot: `aws ec2 get-console-output --instance-id <id> --latest --output text` ou, via SSH, `/var/log/cloud-init-output.log` |
| `git clone` falhou no log | O repositório está público? As mudanças foram enviadas com push? |
| Aba "Servidor" diz que não está na AWS | O `http_put_response_hop_limit` precisa ser `2` (já configurado em `ec2.tf`) |
