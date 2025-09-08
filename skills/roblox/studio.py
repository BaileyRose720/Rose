from pywinauto.application import Application
from time import sleep

class StudioSkill:
    def __init__(self):
        self.app = None
        self.win = None

    def _connect(self):
        if self.win: return
        self.app = Application(backend="uia").connect(path="RobloxStudioBeta.exe")
        self.win = self.app.window(title_re=".*Roblox Studio.*")
        self.win.set_focus()

    async def run(self, intent, params):
        self._connect()
        if intent == "studio_playtest":
            self.win.child_window(title="Test", control_type="TabItem").select()
            self.win.child_window(title="Play", control_type="Button").click_input()
            sleep(5)
            return {"ok": True}
        if intent == "studio_run_tests":
            self.win.child_window(title="Test", control_type="TabItem").select()
            self.win.child_window(title="Run", control_type="Button").click_input()
            sleep(3)
            return {"ok": True}
        if intent == "studio_publish":
            try:
                self.win.menu_select("File->Publish to Roblox")
            except Exception:
                pass
            sleep(2)
            return {"ok": True, "requires_confirmation": True}
        return {"ok": False, "error": "unknown studio intent"}
