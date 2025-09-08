from pathlib import Path

class InboxSkill:
    async def run(self, intent, params):
        if intent == "classify_threads":
            # placeholder: apply simple heuristics or LLM summaries later
            return {"ok": True}
        if intent == "draft_replies":
            Path("runtime/reports").mkdir(parents=True, exist_ok=True)
            Path("runtime/reports/inbox_drafts.md").write_text("# Drafts\n\n- (stub) reply 1\n- (stub) reply 2\n")
            return {"ok": True, "requires_confirmation": True}
        if intent == "propose_events_from_threads":
            return {"ok": True}
        if intent == "generate_digest_pdf":
            Path(params).write_text("Inbox Digest (stub)")
            return {"ok": True}
        if intent == "stop_before_send":
            return {"ok": True, "requires_confirmation": True}
        return {"ok": False, "error": "unknown inbox intent"}
