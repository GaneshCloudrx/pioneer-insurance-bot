#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Configure a Windows VM for unattended UI automation (RDP bots).
.DESCRIPTION
    Applies registry and power settings to prevent screen saver, lock screen,
    idle timeout, and sleep — all of which break foreground UI automation.
    Run once per VM as Administrator.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== Configuring VM for unattended UI automation ===" -ForegroundColor Cyan

# ── Disable screen saver ─────────────────────────────────────────────────────
Write-Host "[1/6] Disabling screen saver..."
Set-ItemProperty -Path "HKCU:\Control Panel\Desktop" -Name "ScreenSaveActive"  -Value "0"
Set-ItemProperty -Path "HKCU:\Control Panel\Desktop" -Name "ScreenSaveTimeOut" -Value "0"

# ── Terminal Services: never disconnect / end idle sessions ───────────────────
$tsPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services"
if (-not (Test-Path $tsPath)) {
    New-Item -Path $tsPath -Force | Out-Null
}

Write-Host "[2/6] Setting Terminal Services idle/disconnect policies..."
Set-ItemProperty -Path $tsPath -Name "MaxIdleTime"           -Value 0 -Type DWord
Set-ItemProperty -Path $tsPath -Name "MaxDisconnectionTime"  -Value 0 -Type DWord
Set-ItemProperty -Path $tsPath -Name "fDisableAutoReconnect" -Value 0 -Type DWord

# ── Disable lock screen ──────────────────────────────────────────────────────
$personPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Personalization"
if (-not (Test-Path $personPath)) {
    New-Item -Path $personPath -Force | Out-Null
}

Write-Host "[3/6] Disabling lock screen..."
Set-ItemProperty -Path $personPath -Name "NoLockScreen" -Value 1 -Type DWord

# ── Disable lock on workstation ──────────────────────────────────────────────
Write-Host "[4/6] Disabling machine inactivity lock..."
$systemPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
if (-not (Test-Path $systemPath)) {
    New-Item -Path $systemPath -Force | Out-Null
}
Set-ItemProperty -Path $systemPath -Name "InactivityTimeoutSecs" -Value 0 -Type DWord

# ── Power plan: never sleep, never turn off display ──────────────────────────
Write-Host "[5/6] Setting power plan to never sleep / never turn off display..."
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0
powercfg /change monitor-timeout-ac 0
powercfg /change monitor-timeout-dc 0
powercfg /change hibernate-timeout-ac 0
powercfg /change hibernate-timeout-dc 0

# ── Disable screen saver via Group Policy registry key ───────────────────────
Write-Host "[6/6] Disabling screen saver via Group Policy..."
$gpScreenSaverPath = "HKCU:\SOFTWARE\Policies\Microsoft\Windows\Control Panel\Desktop"
if (-not (Test-Path $gpScreenSaverPath)) {
    New-Item -Path $gpScreenSaverPath -Force | Out-Null
}
Set-ItemProperty -Path $gpScreenSaverPath -Name "ScreenSaveActive"  -Value "0"
Set-ItemProperty -Path $gpScreenSaverPath -Name "ScreenSaverIsSecure" -Value "0"

Write-Host ""
Write-Host "=== VM configuration complete ===" -ForegroundColor Green
Write-Host "Reminder: use 'tscon %sessionname% /dest:console' before disconnecting RDP." -ForegroundColor Yellow
