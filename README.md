# 🌹 Rose (Windows) — Private, Self‑Hosted AI

This is a Windows‑native starter scaffold for **Rose**, your autonomous AI agent.

## Quick start

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
playwright install
python .\core\agent.py --mission .\ops\missions\inbox_triage.yml
```

> First run opens a browser profile in `runtime/edge_profile` and will create draft files under `runtime/reports`.

## Repo layout

- `core/` — planner, memory, policy engine, model router, takeover server (stub)
- `skills/` — Windows web automation, inbox triage, file cabinet, Roblox Studio control
- `ops/` — policies (scopes/limits) and missions (step lists you can schedule)
- `runtime/` — logs, memory, reports, sandbox
- `tools/` — UI automation + vision helpers