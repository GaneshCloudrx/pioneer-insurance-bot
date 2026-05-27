param(
    [string]$TaskName = "CloudRxDEBot",
    [string]$BotRoot = "C:\Bots\CloudRxDE",
    [string]$PythonExe = "python",
    [string]$RepoUrl = "https://github.com/GaneshCloudrx/cloudrx-dataentry-bot.git",
    [string]$Branch = "main",
    [string]$UserName
)

if (-not $UserName) {
    throw "UserName is required. Example: .\register_task.ps1 -UserName BOTUSER"
}

$appPath = Join-Path $BotRoot "app"
$mainPath = Join-Path $appPath "main.py"
$startScriptPath = Join-Path $BotRoot "deploy\start_bot.ps1"

$argumentParts = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$startScriptPath`"",
    "-BotRoot", "`"$BotRoot`"",
    "-PythonExe", "`"$PythonExe`"",
    "-RepoUrl", "`"$RepoUrl`"",
    "-Branch", "`"$Branch`""
)

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument ($argumentParts -join " ")

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $UserName

$principal = New-ScheduledTaskPrincipal `
    -UserId $UserName `
    -LogonType Interactive `
    -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

$task = New-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings

Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force
Write-Host "Scheduled task '$TaskName' registered for user '$UserName'."
