# window_capture.py

import win32gui
import win32ui
import win32con
from PIL import Image

def get_title_bar_height(hwnd):
    client_rect = win32gui.GetClientRect(hwnd)
    win_rect = win32gui.GetWindowRect(hwnd)
    
    # Calculate the sizes of the window borders.
    border_width = (win_rect[2] - win_rect[0] - client_rect[2]) // 2
    title_bar_height = (win_rect[3] - win_rect[1] - client_rect[3]) - border_width
    return title_bar_height

def find_dosbox_window():
    def callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd)
        if "DOSBOX" in title.upper() and "INDYCAR" in title.upper():
            extra.append(hwnd)
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else None


def capture_window(hwnd):
    client_rect = win32gui.GetClientRect(hwnd)
    win_rect = win32gui.GetWindowRect(hwnd)

    # Calculate the sizes of the window borders.
    border_width = (win_rect[2] - win_rect[0] - client_rect[2]) // 2
    title_bar_height = (win_rect[3] - win_rect[1] - client_rect[3]) - border_width

    # Capture area dimensions
    capture_width = client_rect[2]
    capture_height = client_rect[3]

    # Capture starting point
    src_x = border_width
    src_y = title_bar_height

    # Capture the screenshot
    hwinDC = win32gui.GetWindowDC(hwnd)
    srcDC = win32ui.CreateDCFromHandle(hwinDC)
    memDC = srcDC.CreateCompatibleDC()
    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(srcDC, capture_width, capture_height)
    memDC.SelectObject(screenshot)
    memDC.BitBlt((0, 0), (capture_width, capture_height), srcDC, (src_x, src_y), win32con.SRCCOPY)

    # Convert the resulting image
    bmpinfo = screenshot.GetInfo()
    bmpstr = screenshot.GetBitmapBits(True)
    image = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1
    )

    # Cleanup
    win32gui.DeleteObject(screenshot.GetHandle())
    memDC.DeleteDC()
    srcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwinDC)

    return image