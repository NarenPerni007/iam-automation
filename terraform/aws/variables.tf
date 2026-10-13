variable "region" {
  description = "AWS region for the roles. Used in the deploy policy condition."
  type        = string
  default     = "us-east-1"
}

variable "security_account_id" {
  description = "AWS account ID of the security/audit account allowed to assume the audit role."
  type        = string
}

variable "external_id" {
  description = "External ID the security account must present to assume the audit role."
  type        = string
  sensitive   = true
}

variable "ci_role_arn" {
  description = "ARN of the CI role allowed to assume the deploy role."
  type        = string
}

variable "deploy_bucket_arn" {
  description = "ARN of the S3 bucket the deploy role may write build artifacts to."
  type        = string
}

variable "log_group_arn" {
  description = "ARN of the CloudWatch log group the deploy role may write to."
  type        = string
}

variable "tags" {
  description = "Tags applied to the roles."
  type        = map(string)
  default     = {}
}
