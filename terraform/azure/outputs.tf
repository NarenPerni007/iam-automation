output "reader_role_id" {
  description = "Resource ID of the Platform Reader role definition."
  value       = azurerm_role_definition.reader.id
}

output "deployer_role_id" {
  description = "Resource ID of the Platform Deployer role definition."
  value       = azurerm_role_definition.deployer.id
}
