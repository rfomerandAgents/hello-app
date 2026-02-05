# Outputs for {{PROJECT_NAME}} Infrastructure

output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.app.id
}

output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = local.public_ip
}

output "public_dns" {
  description = "Public DNS name assigned by AWS"
  value       = aws_instance.app.public_dns
}

output "website_url" {
  description = "HTTP URL to access the website"
  value       = "http://${local.public_ip}"
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/id_rsa ubuntu@${local.public_ip}"
  sensitive   = false
}

output "ami_id" {
  description = "AMI ID used for the instance deployment"
  value       = local.ami_id
}

output "website_url_https" {
  description = "HTTPS URL to access the website"
  value       = "https://${local.public_ip}"
}

output "domain_url" {
  description = "Environment-specific domain URL"
  value = (
    var.environment == "prod" ? "https://{{DOMAIN}}" :
    var.environment == "sandbox" ? "https://sandbox.{{DOMAIN}}" :
    var.environment == "staging" ? "https://staging.{{DOMAIN}}" :
    "https://dev.{{DOMAIN}}"
  )
}

output "ssl_configured" {
  description = "Indicates whether SSL certificates are configured"
  value       = var.ssl_cert != "" && var.ssl_key != "" ? "Yes" : "No"
  sensitive   = true
}

output "environment" {
  description = "Current deployment environment"
  value       = var.environment
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.app.id
}
