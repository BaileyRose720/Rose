import mss, numpy as np, cv2

def screenshot():
    with mss.mss() as sct:
        m = sct.monitors[1]
        img = np.array(sct.grab(m))[:,:,:3]
        return img

def find_on_screen(template_bgr, thresh: float = 0.92):
    screen = screenshot()
    res = cv2.matchTemplate(screen, template_bgr, cv2.TM_CCOEFF_NORMED)
    _, maxv, _, maxpt = cv2.minMaxLoc(res)
    return (maxv, maxpt)
