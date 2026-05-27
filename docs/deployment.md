# Deployment Workflow

## Repo Package

The repo keeps shared code under `app/` and deployment tooling under `deploy/`.
Machine-specific settings stay outside Git.

## Git Update Steps

1. Push code changes to GitHub.
2. Ensure each target VM has `C:\Bots\CloudRxDE\config\.env`.
3. Ensure each target VM is configured for AutoLogon and has the `CloudRxDEBot` Scheduled Task set to trigger `At log on`.
4. Register the task with `deploy\register_task.ps1` if needed.
5. Restart the VM or run `deploy\update_from_git.ps1 -RestartBotTask`.

## Runtime Data

The deployment preserves local VM data:

- `logs`
- `recordings`
- `reports`
- `queue_export_files`
- `runtime`

Only `C:\Bots\CloudRxDE\app` is refreshed from GitHub during deployment.

## Unattended Execution Model

This bot should run in an interactive Windows session:

- AutoLogon restores the desktop session after reboot
- Scheduled Task starts the bot at user logon
- The task should be configured as `Run only when user is logged on`

This avoids issues with Pioneer UI access, coordinate-based clicks, screenshots, and screen recording in non-interactive sessions.
