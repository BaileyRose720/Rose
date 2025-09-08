import asyncio, json, sys
from pathlib import Path
from core.planner import Planner
from core.policies import PolicyEngine
from core.memory import Memory
from core.router import ModelRouter
from core.takeover_server import start_takeover_server, stop_takeover_server

class Agent:
    def __init__(self, policy_path: Path):
        self.memory = Memory(Path("runtime/memory"))
        self.policy = PolicyEngine(policy_path)
        self.router = ModelRouter()
        self.planner = Planner(self.router, self.memory, self.policy)

    async def run_mission(self, mission_path: Path):
        if mission_path.suffix == ".json":
            mission = json.loads(Path(mission_path).read_text())
        else:
            import yaml
            mission = yaml.safe_load(Path(mission_path).read_text())
        await self.planner.execute(mission)

async def main():
    agent = Agent(Path("ops/policies/default.yml"))
    await start_takeover_server(port=8765)

    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--mission", required=False, default="ops/missions/inbox_triage.yml")
    args = p.parse_args()

    try:
        await agent.run_mission(Path(args.mission))
    finally:
        await stop_takeover_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
