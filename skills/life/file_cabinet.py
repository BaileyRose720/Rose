from pathlib import Path

class FileCabinet:
    async def run(self, intent, params):
        if intent == "organize_downloads":
            return {"ok": True}
        if intent == "extract_pdfs":
            Path(params["csv_out"]).write_text("date,vendor,amount\n")  # stub
            return {"ok": True}
        if intent == "make_weekly_digest":
            Path(params["out"]).write_text("# Files Digest\n(stub)")
            return {"ok": True}
        return {"ok": False, "error": "unknown file_cabinet intent"}
