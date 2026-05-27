# CloudRx Data Entry Bot

Shared Python automation bot for CloudRx Pioneer data entry.

## Repo Layout

- `app/` shared runtime code
- `config/.env.example` template for per-VM settings
- `deploy/` deployment and updater scripts
- `docs/` VM setup and rollout notes

## Deployment Model

- The same code is deployed to every VM from GitHub.
- Each VM keeps its own `config\.env` outside the code package.
- Deployments replace only the `app/` folder.
- Logs, recordings, reports, queue exports, and retry files stay local to each VM.

## Local Development

When running from the repo, the bot uses the repo root as `BOT_ROOT` by default.
For deployed VMs, set `BOT_BASE_DIR=C:\Bots\CloudRxDE` in `.env`.
