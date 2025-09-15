from core.takeover_server import current_mode
import fnmatch, yaml


class PolicyEngine:
    def __init__(self, default_path):
        self.rules = {}
        self.default_path = default_path

    def load(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.rules = yaml.safe_load(f.read()) or {}

    # --- existing helpers ---
    def _allowed_host(self, host):
        allow = self.rules.get("network_allow", [])
        return any(fnmatch.fnmatch(host, pat) for pat in allow)

    def _allowed_path(self, path, mode="write"):
        key = "write" if mode == "write" else "read"
        scopes = (self.rules.get("fs") or {}).get(key, [])
        return any(path.startswith(p) for p in scopes)

    # --- NEW: risk & confirmation ---
    def risk_of(self, intent: str) -> str:
        r = self.rules.get("risk", {})
        if intent in (r.get("high") or []): return "high"
        if intent in (r.get("medium") or []): return "medium"
        return "low"

    def confirm_required(self, intent: str) -> bool:
        # prefer file setting, else live mode from takeover server
        mode = (self.rules.get("mode") or current_mode() or "autonomous").lower()
        risk = self.risk_of(intent)
        if mode == "autonomous":
            return risk == "high"
        if mode == "cautious":
            return risk in ("medium","high")
        return True  # strict

    def guard(self, intent, params):
        # never allow
        if intent in (self.rules.get("forbidden_actions") or []):
            raise PermissionError(f"{intent} is forbidden by policy")

        # network scope (best-effort, only if configured)
#        host = ""
#        if isinstance(params, str): host = params
#        elif isinstance(params, dict):
#            host = params.get("host") or params.get("url","")
#        if "://" in host: host = host.split("://",1)[1].split("/",1)[0]
#        if host and self.rules.get("network_allow") and not self._allowed_host(host):
#            raise PermissionError(f"network host not allowed: {host}")