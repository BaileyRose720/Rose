import fnmatch, yaml

class PolicyEngine:
    def __init__(self, default_path):
        self.rules = {}
        self.default_path = default_path

    def load(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.rules = yaml.safe_load(f.read()) or {}

    def _allowed_host(self, host):
        allow = self.rules.get("network_allow", [])
        return any(fnmatch.fnmatch(host, pat) for pat in allow)

    def _allowed_path(self, path, mode="write"):
        key = "write" if mode == "write" else "read"
        scopes = (self.rules.get("fs") or {}).get(key, [])
        # naive prefix check (Windows paths with backslashes)
        return any(path.startswith(p) for p in scopes)

    def guard(self, intent, params):
        # ban destructive actions
        if intent in (self.rules.get("forbidden_actions") or []):
            raise PermissionError(f"{intent} is forbidden by policy")

        # Basic network host check
        host = ""
        if isinstance(params, str):
            host = params
        elif isinstance(params, dict):
            host = params.get("host") or params.get("url","")
        if "://" in host:
            host = host.split("://",1)[1].split("/",1)[0]
        if host and not self._allowed_host(host):
            # If no network_allow configured, skip
            if self.rules.get("network_allow"):
                raise PermissionError(f"network host not allowed: {host}")
