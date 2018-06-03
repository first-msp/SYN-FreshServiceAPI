Param(
    [string]$Group,
    [string]$FileShare,
    [string]$Email
    )

Import-Module ActiveDirectory

$secpasswd = ConvertTo-SecureString "72B4fbc361!" -AsPlainText -Force
$mycreds = New-Object System.Management.Automation.PSCredential ("administrator", $secpasswd)

$pos = $Email.IndexOf("@")
$Username = $Email.Substring(0, $pos)
$Domain = $Email.Substring($pos+1)

Add-ADGroupMember -Identity $FileShare -Members $Username -Credential $mycreds -Server 192.168.0.40
Write-Host "Adding " $Username " to " $FileShare