import time, asyncio
from typing import Dict, Any, List
from core.takeover import takeover

class Planner:
    def __init__(self, router, memory, policy):
        self.router, self.memory, self.policy = router, memory, policy
        self._web = None  # keep refs to close gracefully later

    async def execute(self, mission: Dict[str, Any]):
        steps: List[Dict[str, Any]] = mission.get("steps", [])
        policy_path = mission.get("policy", "ops/policies/default.yml")
        ctx = {"mission": mission.get("name","unnamed"), "start": time.time(), "steps_done": 0}
        self.policy.load(policy_path)

        # Lazy imports
        from skills.general.playwright_web import WebSkill
        from skills.life.inbox_triage import InboxSkill
        from skills.life.file_cabinet import FileCabinet
        from skills.roblox.studio import StudioSkill

        self._web = WebSkill()
        inbox = InboxSkill()
        files = FileCabinet()
        studio = StudioSkill()

        for step in steps:
            intent = list(step.keys())[0]
            params = step[intent]
            self.policy.guard(intent, params)

            if intent in ("open_app","navigate","click","type","dom"):
                result = await self._web.run(intent, params)
            elif intent in ("classify_threads","draft_replies","propose_events_from_threads","generate_digest_pdf","stop_before_send"):
                result = await inbox.run(intent, params)
            elif intent in ("organize_downloads","extract_pdfs","make_weekly_digest"):
                result = await files.run(intent, params)
            elif intent in ("studio_playtest","studio_publish","studio_run_tests"):
                result = await studio.run(intent, params)
            else:
                result = {"ok": False, "error": f"unknown intent {intent}"}

            ctx["steps_done"] += 1
            self.memory.summarize_step(ctx["mission"], intent, params, result)

            if result.get("requires_confirmation"):
                # 🔴 actually pause and wait for you to click Approve/Cancel
                approved = await request_decision(f"Step '{intent}' needs approval.")
                if not approved:
                    # mark run cancelled but keep things tidy
                    break

        self.memory.finalize_run(ctx["mission"], ctx)

    async def close(self):
        # allow the agent to shut down cleanly (browser etc.)
        if self._web:
            try:
                await self._web.close()
            except Exception:
                pass
