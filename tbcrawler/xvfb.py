from pyvirtualdisplay import Display
import common as cm


def start_xvfb(win_width=cm.DEFAULT_XVFB_WIN_W,
               win_height=cm.DEFAULT_XVFB_WIN_H):
    xvfb_display = Display(visible=0, size=(win_width, win_height))
    xvfb_display.start()
    return xvfb_display


def stop_xvfb(xvfb_display):
    if xvfb_display:
        xvfb_display.stop()
