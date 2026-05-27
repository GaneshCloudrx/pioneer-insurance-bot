# Deployment

## Recommended VM Model

Use GitHub as the source of truth and let each VM refresh `app\` locally before the bot starts.

This keeps the current folder structure and preserves:

- `C:\Bots\CloudRxDE\config\.env`
- local runtime folders outside `app\`
- the existing `CloudRxDEBot` logon trigger model

## One-Time Setup On Each VM

Requirements:

- Git is installed and available in `PATH`
- Python is already installed on each VM
- `C:\Bots\CloudRxDE\config\.env` already exists
- `C:\Bots\CloudRxDE\config\.env` should include `GITHUB_TOKEN=<read-only token>` for private repos
- AutoLogon is already configured for the bot Windows account

Register the bot task:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Bots\CloudRxDE\deploy\register_task.ps1" -UserName "localadmin" -PythonExe "C:\Users\localadmin\AppData\Local\Programs\Python\Python313\python.exe"
```

What this does now:

- runs `deploy\update_from_git.ps1`
- syncs `app\` and `deploy\` from GitHub
- installs `app\requirements.txt`
- starts `app\main.py`

## Normal Update Flow

1. Push code to GitHub.
2. Restart the VM or log back into the bot user session.
3. The existing task pulls the latest code before starting the bot.

## Manual Hotfix Update Without Restart

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Bots\CloudRxDE\deploy\update_from_git.ps1" -PythonExe "C:\Users\localadmin\AppData\Local\Programs\Python\Python313\python.exe" -RestartBotTask
```

## Notes

- The updater uses `https://github.com/GaneshCloudrx/cloudrx-dataentry-bot.git`
- For private repos, the updater reads `GITHUB_TOKEN` from `config\.env` or the VM environment
- The updater does a fresh clone of the latest branch into `deploy\repo-cache` on each run
- `app\` is refreshed from GitHub
- `config\.env` is never pulled from GitHub
- The updater keeps a backup copy in `C:\Bots\CloudRxDE\backup\app_previous`
- The last deployed commit is written to `C:\Bots\CloudRxDE\runtime\version.txt`
- Update logs are appended to `C:\Bots\CloudRxDE\logs\git-update.log`
