import win32gui
import win32ui
import win32con
from PIL import Image


def get_title_bar_height(hwnd):
    client_rect = win32gui.GetClientRect(hwnd)
    win_rect = win32gui.GetWindowRect(hwnd)
    border_width = (win_rect[2] - win_rect[0] - client_rect[2]) // 2
    title_bar_height = (win_rect[3] - win_rect[1] - client_rect[3]) - border_width
    return title_bar_height


def find_icr2_window(app_keywords, mode="any"):
    """
    Find the ICR2 game window by title.

    Args:
        app_keywords (list[str]): Keywords to search for in window titles.
        mode (str): 'any' or 'all'.
            - 'any': match if any keyword appears in the title.
            - 'all': match only if all keywords appear in the title.

    Returns:
        tuple: (hwnd, title) or (None, None)
    """
    def callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd).upper()
        if not title:
            return

        if mode == "any":
            if any(word in title for word in app_keywords):
                extra.append((hwnd, title))
        elif mode == "all":
            if all(word in title for word in app_keywords):
                extra.append((hwnd, title))

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else (None, None)


def capture_window(hwnd):
    client_rect = win32gui.GetClientRect(hwnd)
    win_rect = win32gui.GetWindowRect(hwnd)

    border_width = (win_rect[2] - win_rect[0] - client_rect[2]) // 2
    title_bar_height = (win_rect[3] - win_rect[1] - client_rect[3]) - border_width

    capture_width = client_rect[2]
    capture_height = client_rect[3]

    src_x = border_width
    src_y = title_bar_height

    hwinDC = win32gui.GetWindowDC(hwnd)
    srcDC = win32ui.CreateDCFromHandle(hwinDC)
    memDC = srcDC.CreateCompatibleDC()
    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(srcDC, capture_width, capture_height)
    memDC.SelectObject(screenshot)
    memDC.BitBlt((0, 0), (capture_width, capture_height), srcDC, (src_x, src_y), win32con.SRCCOPY)

    bmpinfo = screenshot.GetInfo()
    bmpstr = screenshot.GetBitmapBits(True)
    image = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1
    )

    win32gui.DeleteObject(screenshot.GetHandle())
    memDC.DeleteDC()
    srcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwinDC)

    return image

def find_window_with_keywords(keywords, mode="any"):
    """
    Look for any window that matches the given keywords.

    Returns:
        (hwnd, title) or (None, None)
    """
    def callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd).upper()
        if not title:
            return
        if mode == "any" and any(word in title for word in keywords):
            extra.append((hwnd, title))
        elif mode == "all" and all(word in title for word in keywords):
            extra.append((hwnd, title))

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else (None, None)
