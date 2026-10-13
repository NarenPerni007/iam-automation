output "audit_role_arn" {
  description = "ARN of the read-only audit role."
  value       = aws_iam_role.audit.arn
}

output "deploy_role_arn" {
  description = "ARN of the scoped deploy role."
  value       = aws_iam_role.deploy.arn
}
