# 🌹 Rose (Windows) — Private, Self‑Hosted AI Agent

This is a Windows‑native starter scaffold for **Rose**, your autonomous AI agent.
It mirrors ByteBot’s agent architecture (planner → skills → takeover), but uses Windows UI Automation and Playwright instead of a Linux desktop container.

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

## License

Rose starter is MIT. If you *copy* any ByteBot source later, keep Apache‑2.0 headers and add to `THIRD_PARTY_NOTICES.txt`.
