output "instance_public_ip" {
  description = "IP público da instância"
  value       = module.compute.public_ip
}

output "app_url" {
  description = "URL do app Streamlit"
  value       = "http://${module.compute.public_ip}:8501"
}
