import asyncio, json, sys, os, traceback, contextlib
from pathlib import Path
from core.planner import Planner
from core.policies import PolicyEngine
from core.memory import Memory
from core.router import ModelRouter
from core.takeover_server import start_takeover_server

# If Playwright ever misbehaves on Windows, this loop policy is safer.
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

class Agent:
    def __init__(self, policy_path: Path):
        self.memory = Memory(Path("runtime/memory"))
        self.policy = PolicyEngine(policy_path)
        self.router = ModelRouter()
        self.planner = Planner(self.router, self.memory, self.policy)

    async def run_mission(self, mission_path: Path):
        import yaml
        mission = yaml.safe_load(Path(mission_path).read_text())
        await self.planner.execute(mission)

async def main():
    agent = Agent(Path("ops/policies/default.yml"))

    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--mission", required=False, default="ops/missions/inbox_triage.yml")
    p.add_argument("--no-server", action="store_true", help="Skip starting the takeover server")
    args = p.parse_args()

    # Allow skipping the server via env var too
    no_server = args.no_server or os.environ.get("ROSE_NO_SERVER") == "1"

    crashed = False

    # 1) Run the mission first; if it fails, show the real error and exit.
    try:
        if args.mission:
            print(f"[Agent] Running mission: {args.mission}")
            await agent.run_mission(Path(args.mission))
        else:
            print("[Agent] No --mission provided; idle mode.")
    except Exception:
        crashed = True
        print("\n=== FATAL: mission crashed ===")
        traceback.print_exc()
    finally:
        # Close planner regardless of success/failure
        with contextlib.suppress(Exception):
            await agent.planner.close()

    # 2) Only start the takeover server if mission succeeded and we're not skipping it.
    if not crashed and not no_server:
        print("[Agent] Starting takeover server on :8765 (Ctrl+C to stop)…")
        server_task = asyncio.create_task(start_takeover_server(port=8765))
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)