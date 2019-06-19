# Create a column master key in Azure Key Vault.

# Connect-AzAccount

# $SubscriptionId = "3af10acd-5d13-46b3-897f-ce1a3239d8ac"
# $resourceGroup = "Default"
# $azureLocation = "East Asia"
# $akvName = "db-kalepso-azure"
# $akvKeyName = "my-key"
# $azureCtx = Set-AzConteXt -SubscriptionId $SubscriptionId # Sets the context for the below cmdlets to the specified subscription.
# New-AzResourceGroup -Name $resourceGroup -Location $azureLocation # Creates a new resource group - skip, if you desire group already exists.
# New-AzKeyVault -VaultName $akvName -ResourceGroupName $resourceGroup -Location $azureLocation # Creates a new key vault - skip if your vault already exists.
# Set-AzKeyVaultAccessPolicy -VaultName $akvName -ResourceGroupName $resourceGroup -PermissionsToKeys get, create, delete, list, update, import, backup, restore, wrapKey, unwrapKey, sign, verify -UserPrincipalName $azureCtx.Account
# $akvKey = Add-AzureKeyVaultKey -VaultName $akvName -Name $akvKeyName -Destination "Software"

$keyId = "https://kalepso-bench.vault.azure.net/keys/my-key-2/d20aefb0699f4744a6b0dcf2b2c5e602"

# Write-Output "Key generated."
# Write-Output $akvKey.ID

# Import the SQL Server Module
Import-Module "SqlServer"

# Connect to your database.
$serverName = "128.197.11.210,1433"
$databaseName = "master"
$userId = "sa"
$password = "Password123!"
$connStr = "Server = " + $serverName + "; Database = " + $databaseName + "; User ID = " + $userId + "; Password = " + $password + ";"
$connection = New-Object Microsoft.SqlServer.Management.Common.ServerConnection
$connection.ConnectionString = $connStr
$connection.Connect()
$server = New-Object Microsoft.SqlServer.Management.Smo.Server($connection)
$database = $server.Databases[$databaseName] 

Write-Output "Connected."
Write-Output $connStr

# Create a SqlColumnMasterKeySettings object for your column master key.
$cmkSettings = New-SqlAzureKeyVaultColumnMasterKeySettings -KeyURL $keyId

Write-Output "Generated settings."

# Create column master key metadata in the database.
$cmkName = "CMK1"
# New-SqlColumnMasterKey -Name $cmkName -InputObject $database -ColumnMasterKeySettings $cmkSettings

Write-Output "Generated master key."

# Authenticate to Azure
Add-SqlAzureAuthenticationContext -Interactive

Write-Output "Authenticated."

# Generate a column encryption key, encrypt it with the column master key and create column encryption key metadata in the database. 
$cekName = "CEK1"
New-SqlColumnEncryptionKey -Name $cekName -InputObject $database -ColumnMasterKey $cmkName

Write-Output "Generated column encryption key."

# List column master keys for the specified database.
Get-SqlColumnMasterKey -InputObject $database

Write-Output "Done."
