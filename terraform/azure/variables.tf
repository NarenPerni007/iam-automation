variable "subscription_id" {
  description = "Subscription the custom roles are assignable in."
  type        = string
}

variable "reader_principal_id" {
  description = "Object ID of the user, group, or service principal getting the Platform Reader role."
  type        = string
}

variable "deployer_principal_id" {
  description = "Object ID of the user, group, or service principal getting the Platform Deployer role."
  type        = string
}
