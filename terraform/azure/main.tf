provider "azurerm" {
  features {}
}

# Platform Reader: read access to the resources a platform team watches.
# No write, no secrets, no role assignments.
resource "azurerm_role_definition" "reader" {
  name        = "Platform Reader"
  description = "Read access to platform resources. No write access."
  scope       = "/subscriptions/${var.subscription_id}"

  permissions {
    actions = [
      "Microsoft.Resources/subscriptions/resourceGroups/read",
      "Microsoft.Compute/virtualMachines/read",
      "Microsoft.ContainerService/managedClusters/read",
      "Microsoft.Network/virtualNetworks/read",
      "Microsoft.Network/networkSecurityGroups/read",
      "Microsoft.Storage/storageAccounts/read",
      "Microsoft.Insights/components/read"
    ]
    not_actions = []
  }

  assignable_scopes = ["/subscriptions/${var.subscription_id}"]
}

# Platform Deployer: enough to deploy and manage platform workloads, but
# no identity or access management. Nobody gets roleAssignments/write here.
resource "azurerm_role_definition" "deployer" {
  name        = "Platform Deployer"
  description = "Deploy and manage platform workloads. No access management."
  scope       = "/subscriptions/${var.subscription_id}"

  permissions {
    actions = [
      "Microsoft.Resources/subscriptions/resourceGroups/read",
      "Microsoft.Resources/deployments/write",
      "Microsoft.Resources/deployments/read",
      "Microsoft.ContainerService/managedClusters/read",
      "Microsoft.ContainerService/managedClusters/write",
      "Microsoft.Network/networkSecurityGroups/read",
      "Microsoft.Network/networkSecurityGroups/write",
      "Microsoft.Network/virtualNetworks/read",
      "Microsoft.Storage/storageAccounts/read",
      "Microsoft.Storage/storageAccounts/write",
      "Microsoft.Insights/components/read",
      "Microsoft.Insights/components/write"
    ]
    not_actions = []
  }

  assignable_scopes = ["/subscriptions/${var.subscription_id}"]
}

resource "azurerm_role_assignment" "reader" {
  scope              = "/subscriptions/${var.subscription_id}"
  role_definition_id = azurerm_role_definition.reader.role_definition_resource_id
  principal_id       = var.reader_principal_id
}

resource "azurerm_role_assignment" "deployer" {
  scope              = "/subscriptions/${var.subscription_id}"
  role_definition_id = azurerm_role_definition.deployer.role_definition_resource_id
  principal_id       = var.deployer_principal_id
}
