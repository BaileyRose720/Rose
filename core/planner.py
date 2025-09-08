import time, asyncio
from typing import Dict, Any, List

class Planner:
    def __init__(self, router, memory, policy):
        self.router, self.memory, self.policy = router, memory, policy

    async def execute(self, mission: Dict[str, Any]):
        steps: List[Dict[str, Any]] = mission.get("steps", [])
        policy_path = mission.get("policy", "ops/policies/default.yml")
        ctx = {"mission": mission.get("name","unnamed"), "start": time.time(), "steps_done": 0}
        self.policy.load(policy_path)

        # Lazy imports to keep startup snappy
        from skills.general.playwright_web import WebSkill
        from skills.life.inbox_triage import InboxSkill
        from skills.life.file_cabinet import FileCabinet
        from skills.roblox.studio import StudioSkill

        web = WebSkill()
        inbox = InboxSkill()
        files = FileCabinet()
        studio = StudioSkill()

        for step in steps:
            intent = list(step.keys())[0]
            params = step[intent]

            # policy pre-checks (network/fs scopes, forbidden actions)
            self.policy.guard(intent, params)

            if intent in ("open_app","navigate","click","type","dom"):
                result = await web.run(intent, params)
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
                # In a fuller build, notify takeover UI; for now just pause
                print(f"[TAKEOVER] Waiting for confirmation on step: {intent}")
                await asyncio.sleep(0.1)

        self.memory.finalize_run(ctx["mission"], ctx)
