output "instance_public_ip" {
  description = "IP público da instância"
  value       = aws_instance.web.public_ip
}

output "app_url" {
  description = "URL do app Streamlit"
  value       = "http://${aws_instance.web.public_ip}:8501"
}
