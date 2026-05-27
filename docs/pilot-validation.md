# Pilot Validation Checklist

Use this checklist on the first two VMs before scaling to the remaining fleet.

## Pre-Deploy

- `.env` exists at `C:\Bots\CloudRxDE\config\.env`
- Pioneer shortcut path is valid on the VM
- VM resolution and scaling match bot expectations
- Python is installed and dependencies are available
- AutoLogon is enabled for the bot Windows account
- Scheduled Task `CloudRxDEBot` exists with trigger `At log on`
- Scheduled Task is configured as `Run only when user is logged on`

## Post-Deploy

- Bot starts from `C:\Bots\CloudRxDE\app\main.py`
- Bot logs use the correct VM-specific Pioneer credentials
- Recordings save under `C:\Bots\CloudRxDE\recordings`
- Reports save under `C:\Bots\CloudRxDE\reports`
- Queue exports save under `C:\Bots\CloudRxDE\queue_export_files`
- Exported queue files are deleted after processing
- `retry.txt` is created under `C:\Bots\CloudRxDE\runtime`
- No runtime files are written back into the repo checkout

## Functional Checks

- Login to Pioneer succeeds
- Queue download succeeds
- Patient filtering still works
- Row selection still works with the pilot VM display setup
- Retry flow still appends to `retry.txt`
- Stop-time logic still sends the bot to END state
