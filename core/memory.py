from pathlib import Path
import json, time

class Memory:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def summarize_step(self, mission_name, intent, params, result):
        rec = {
            "ts": time.time(),
            "mission": mission_name,
            "intent": intent,
            "params": params,
            "result": result,
        }
        (self.root / f"{mission_name.replace(' ','_')}.log.jsonl").open("a", encoding="utf-8").write(json.dumps(rec) + "\n")

    def finalize_run(self, mission_name, ctx):
        rec = {"ts": time.time(), "mission": mission_name, "summary": f"steps={ctx.get('steps_done')}"}
        (self.root / f"{mission_name.replace(' ','_')}.summary.jsonl").open("a", encoding="utf-8").write(json.dumps(rec) + "\n")
