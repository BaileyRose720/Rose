from pywinauto.application import Application

def focus_window(title_regex: str = ".*"):
    app = Application(backend="uia").connect(title_re=title_regex)
    w = app.top_window()
    w.set_focus()
    return w
