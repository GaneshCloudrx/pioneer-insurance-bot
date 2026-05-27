param(
    [string]$RepoUrl = "https://github.com/GaneshCloudrx/cloudrx-dataentry-bot.git",
    [string]$Branch = "main",
    [string]$BotRoot = "C:\Bots\CloudRxDE",
    [string]$PythonExe = "python",
    [string]$TaskName = "CloudRxDEBot",
    [string]$GitHubToken,
    [switch]$RestartBotTask
)

$ErrorActionPreference = "Stop"

$deployPath = Join-Path $BotRoot "deploy"
$repoCachePath = Join-Path $deployPath "repo-cache"
$appPath = Join-Path $BotRoot "app"
$sourceAppPath = Join-Path $repoCachePath "app"
$backupPath = Join-Path $BotRoot "backup\app_previous"
$configEnvPath = Join-Path $BotRoot "config\.env"
$runtimePath = Join-Path $BotRoot "runtime"
$versionPath = Join-Path $runtimePath "version.txt"
$logPath = Join-Path (Join-Path $BotRoot "logs") "git-update.log"

function Write-Log {
    param([string]$Message)

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "$timestamp $Message"
    Write-Host $line
    Add-Content -Path $logPath -Value $line
}

function Invoke-External {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$FailureMessage,
        [switch]$AllowRobocopyExitCodes
    )

    & $FilePath @Arguments
    $exitCode = $LASTEXITCODE

    if ($AllowRobocopyExitCodes) {
        if ($exitCode -gt 7) {
            throw "$FailureMessage Exit code: $exitCode"
        }
        return
    }

    if ($exitCode -ne 0) {
        throw "$FailureMessage Exit code: $exitCode"
    }
}

function Get-ConfigValue {
    param(
        [string]$Path,
        [string]$Key
    )

    if (-not (Test-Path $Path)) {
        return $null
    }

    foreach ($rawLine in Get-Content -Path $Path) {
        $line = $rawLine.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            continue
        }

        $parts = $line.Split("=", 2)
        if ($parts[0].Trim() -eq $Key) {
            return $parts[1].Trim()
        }
    }

    return $null
}

function Get-GitArguments {
    param([string[]]$Arguments)

    return @(
        "-c",
        "credential.helper=",
        "-c",
        "core.askPass="
    ) + $Arguments
}

New-Item -ItemType Directory -Force -Path $BotRoot | Out-Null
New-Item -ItemType Directory -Force -Path $deployPath | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BotRoot "backup") | Out-Null
New-Item -ItemType Directory -Force -Path $runtimePath | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BotRoot "logs") | Out-Null

$gitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $gitCommand) {
    throw "Git is not installed or not available in PATH."
}

$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE = "Never"

if (-not $GitHubToken) {
    $GitHubToken = $env:GITHUB_TOKEN
}

if (-not $GitHubToken) {
    $GitHubToken = Get-ConfigValue -Path $configEnvPath -Key "GITHUB_TOKEN"
}

$gitRepoUrl = $RepoUrl
if ($GitHubToken -and $RepoUrl -like "https://github.com/*") {
    $escapedToken = [Uri]::EscapeDataString($GitHubToken)
    $gitRepoUrl = $RepoUrl -replace '^https://github\.com/', "https://x-access-token:$escapedToken@github.com/"
    Write-Log "Using GitHub token for fresh clone."
}
elseif ($RepoUrl -like "https://github.com/*") {
    Write-Log "No GitHub token found. Git clone may fail for private repos."
}

Write-Log "Starting Git update from $RepoUrl ($Branch)."

$shouldRestartTask = $false

if ($RestartBotTask) {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        $shouldRestartTask = $true
        Write-Log "Stopping scheduled task $TaskName before update."
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    }
}

try {
    if (Test-Path $repoCachePath) {
        Write-Log "Removing previous repo cache."
        Remove-Item -Path $repoCachePath -Recurse -Force
    }

    Write-Log "Cloning latest $Branch into $repoCachePath."
    Invoke-External -FilePath $gitCommand.Source `
        -Arguments (Get-GitArguments @("clone", "--depth", "1", "--branch", $Branch, "--single-branch", $gitRepoUrl, $repoCachePath)) `
        -FailureMessage "Git clone failed."

    if (-not (Test-Path $sourceAppPath)) {
        throw "Source app folder not found in repo cache: $sourceAppPath"
    }

    if (Test-Path $appPath) {
        Write-Log "Updating backup copy of app folder."
        New-Item -ItemType Directory -Force -Path $backupPath | Out-Null
        Invoke-External -FilePath "robocopy.exe" `
            -Arguments @(
                $appPath,
                $backupPath,
                "/MIR",
                "/R:2",
                "/W:2",
                "/NP",
                "/XD",
                "logs",
                "reports",
                "recordings",
                "queue_export_files",
                "runtime",
                "__pycache__",
                "/XF",
                "*.pyc"
            ) `
            -FailureMessage "Backup copy failed." `
            -AllowRobocopyExitCodes
    }

    Write-Log "Syncing repo app folder into $appPath."
    New-Item -ItemType Directory -Force -Path $appPath | Out-Null
    Invoke-External -FilePath "robocopy.exe" `
        -Arguments @(
            $sourceAppPath,
            $appPath,
            "/MIR",
            "/R:2",
            "/W:2",
            "/NP",
            "/XD",
            "logs",
            "reports",
            "recordings",
            "queue_export_files",
            "runtime",
            "__pycache__",
            "/XF",
            "*.pyc"
        ) `
        -FailureMessage "App sync failed." `
        -AllowRobocopyExitCodes

    $requirementsPath = Join-Path $appPath "requirements.txt"
    if (Test-Path $requirementsPath) {
        Write-Log "Installing Python requirements."
        Invoke-External -FilePath $PythonExe `
            -Arguments @("-m", "pip", "install", "-r", $requirementsPath) `
            -FailureMessage "pip install failed."
    }

    $updatedAt = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $commitSha = (& $gitCommand.Source -C $repoCachePath rev-parse HEAD).Trim()
    $versionContent = @(
        "updated_at=$updatedAt"
        "branch=$Branch"
        "commit=$commitSha"
        "repo=$RepoUrl"
    )
    Set-Content -Path $versionPath -Value $versionContent
    Write-Log "Update complete. Commit: $commitSha"
}
finally {
    if ($shouldRestartTask) {
        Write-Log "Starting scheduled task $TaskName."
        Start-ScheduledTask -TaskName $TaskName
    }
}
