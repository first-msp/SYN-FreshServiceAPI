Param(
    [string]$ComputerName,
    [string]$Group,
    [string]$Username,
    [string]$LogLocation
    )

Import-Module ActiveDirectory

$secpasswd = ConvertTo-SecureString "72B4fbc361!" -AsPlainText -Force
$mycreds = New-Object System.Management.Automation.PSCredential ("administrator", $secpasswd)

Add-ADGroupMember -Identity $Group -Members $Username -Credential $mycreds -Server 192.168.0.40