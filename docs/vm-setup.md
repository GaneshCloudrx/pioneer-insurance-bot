# VM Setup

## Standard VM Folders

Create these folders on each VM:

- `C:\Bots\CloudRxDE\config`
- `C:\Bots\CloudRxDE\logs`
- `C:\Bots\CloudRxDE\recordings`
- `C:\Bots\CloudRxDE\reports`
- `C:\Bots\CloudRxDE\queue_export_files`
- `C:\Bots\CloudRxDE\runtime`
- `C:\Bots\CloudRxDE\backup`
- `C:\Bots\CloudRxDE\deploy`

## Config

Create the machine-specific file:

- `C:\Bots\CloudRxDE\config\.env`

Use `config/.env.example` from the repo as the template.

## Unattended Mode

For unattended UI automation, the VM must have an interactive desktop session available.

- Configure Windows AutoLogon for the bot user on the VM
- Use the same Windows user for Pioneer access and bot execution
- Do not use a non-interactive/background task mode for the bot

Recommended approach:

- AutoLogon signs the bot user into Windows after restart
- Scheduled Task triggers `At log on`
- Task is configured as `Run only when user is logged on`

This is important because `pywinauto`, screen recording, coordinate clicks, and Pioneer UI automation need a live desktop session.

## App Launcher / Scheduled Task

Recommended scheduled task command:

```powershell
python C:\Bots\CloudRxDE\app\main.py
```

Or use the full Python path if required by the VM.

Recommended task settings:

- Task name: `CloudRxDEBot`
- Trigger: `At log on`
- User: bot Windows account
- Security option: `Run only when user is logged on`
- Run level: `Highest privileges`

You can use `deploy\register_task.ps1` to create the task consistently.

## VM Requirements

- Pioneer installed and accessible through `PioneerRx.lnk`
- Same resolution/scaling expected by the bot
- Python dependencies installed from `app\requirements.txt`
