"""
ICR2 Overlay Tool
Dependencies: PyQt5, PIL (Pillow), win32gui
"""

# Standard Library Imports
import sys
import win32gui
import time
import configparser
import keyboard

# Local Module Imports
from window_capture import find_dosbox_window, capture_window, get_title_bar_height
from overlay import CockpitOverlay
from image_processing import crop_black_borders_with_coords, is_in_cockpit_view
from dashboard_reader import read_dashboard, plot_lcd_locations

# External Library Imports
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, Qt

class GameState:
    """Holds and updates the game's current state."""
    def __init__(self):
        # Initial values for game state variables
        self.rpm = 0
        self.temp = 0
        self.fuel = 0
        self.mph = 0
        self.gear = 1
        self.cur_boost = 30

        self.f_rollbar = 0
        self.r_rollbar = 0
        self.brake = 0
 
        self.last_update_time = time.time()

    def update(self, rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake):
        """Update the game state based on new readings."""
        self.rpm = rpm
        self.temp = temp
        self.fuel = fuel
        self.mph = mph
        self.gear = gear
        self.f_rollbar = f_rollbar
        self.r_rollbar = r_rollbar
        self.brake = brake
        self.update_boost(boost)

    def update_boost(self, boost_reading):
        """Adjusts the boost value based on the current reading."""
        current_time = time.time()
        time_delta = current_time - self.last_update_time

        if boost_reading < self.cur_boost:
            self.cur_boost -= self.boost_drop_rate_per_second * time_delta
        elif boost_reading > self.cur_boost:
            self.cur_boost += self.boost_climb_rate_per_second * time_delta

        # Reset boost if deviation is significant
        if abs(boost_reading - self.cur_boost) > 15:
            self.cur_boost = boost_reading

        # Update the last update time
        self.last_update_time = current_time

def read_cockpit_pixels(icr2dash_ini_path):
    """Reads cockpit pixel locations from INI file."""
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(icr2dash_ini_path)

    cockpit_pixels = {}
    if 'Cockpit detection' in config.sections():
        # Extract pixel coordinates and RGB values
        for key in config['Cockpit detection']:
            values = list(map(int, config.get('Cockpit detection', key).split(',')))
            cockpit_pixels[(values[0], values[1])] = tuple(values[2:])
    return cockpit_pixels

def take_screenshot():
    hwnd = find_dosbox_window()
    if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd) and hwnd == win32gui.GetForegroundWindow():

        last_screenshot = capture_window(hwnd)
        cropped_screenshot, coords = crop_black_borders_with_coords(last_screenshot)
    
    plot = plot_lcd_locations(cropped_screenshot)
    
    plot.save("output.png", "PNG")
    print ('Took screenshot')



def handle_dosbox_overlay(hwnd):
    """Manages overlay updates in sync with DOSBox window state."""

    # Validate window handle and update overlay
    if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd) and hwnd == win32gui.GetForegroundWindow():

        last_screenshot = capture_window(hwnd)
        cropped_screenshot, coords = crop_black_borders_with_coords(last_screenshot)
        
        if is_in_cockpit_view(cropped_screenshot, COCKPIT_PIXELS) and cockpit_on == True:
            rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake = read_dashboard(cropped_screenshot)
            gs.update(rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake)
            cockpit_overlay.setGauges(gs.rpm, gs.cur_boost, gs.temp, gs.fuel, gs.mph, gs.gear, gs.f_rollbar, gs.r_rollbar, gs.brake)
            cockpit_overlay.show()
        else:
            cockpit_overlay.hide()

        win_rect = win32gui.GetWindowRect(hwnd)
        win_x, win_y = win_rect[0], win_rect[1]
        title_bar_height = get_title_bar_height(hwnd)

        cockpit_overlay.setPositionAndSize(
            coords[0] + win_x + x_adjustment, 
            coords[1] + win_y + title_bar_height + y_adjustment, 
            coords[2] - coords[0], 
            coords[3] - coords[1]
        )
        cockpit_overlay.update()

    else:
        cockpit_overlay.hide()

def update_loop():
    """Main loop for updating the overlay and handling user inputs."""
    global last_screenshot, x_adjustment, y_adjustment, dosbox_window_opened
    
    hwnd = find_dosbox_window()

    # Ensure DOSBox window is present and handle overlay accordingly
    if hwnd:
        if not dosbox_window_opened:
            dosbox_window_opened = True
            print ('ICR2 DOSBox window detected')
        handle_dosbox_overlay(hwnd)
    else:
        if dosbox_window_opened:
            print ('Script ending')
            cockpit_overlay.hide()  # Hide overlay if DOSBox window is missing
            timer.stop()  # Stop the update loop timer
            QApplication.quit()  # Quit the application
        cockpit_overlay.hide()  # Hide overlay if DOSBox window is missing

# Define callback functions for keyboard events
def adjust_x(value):
    global x_adjustment
    x_adjustment += value
    # Code to handle x_adjustment change

def adjust_y(value):
    global y_adjustment
    y_adjustment += value
    # Code to handle y_adjustment change

def toggle_cockpit_overlay():
    global cockpit_on
    if cockpit_on == True:
        cockpit_on = False
        print ('Toggling cockpit off')
    else:
        cockpit_on = True
        print ('Toggling cockpit on')

# Set up keyboard listeners
keyboard.add_hotkey('ctrl+left', adjust_x, args=(-1,))
keyboard.add_hotkey('ctrl+right', adjust_x, args=(1,))
keyboard.add_hotkey('ctrl+up', adjust_y, args=(-1,))
keyboard.add_hotkey('ctrl+down', adjust_y, args=(1,))
keyboard.add_hotkey('ctrl+o', toggle_cockpit_overlay)
keyboard.add_hotkey('ctrl+s', take_screenshot)

# Main script execution
if __name__ == "__main__":
    print ('ICR2 cockpit overlay script started')
    print ('Configurations can be edited in icr2dash.ini and dash_reader.ini')
    print ('Leave this program running in the background when you run ICR2 in DOSBox')
    print ('Once you are in ICR2, Ctrl-arrow keys to adjust overlay. Ctrl-S to take a screenshot with LCD reading points.')

    # Initialize global variables
    last_screenshot = None
    dosbox_window_opened = False
    icr2dash_ini_path = 'icr2dash.ini'
    cockpit_on = True

    # Load configuration
    config = configparser.ConfigParser()
    config.read(icr2dash_ini_path)
    x_adjustment = config.getint('Overlay positioning', 'x_adjustment')
    y_adjustment = config.getint('Overlay positioning', 'y_adjustment')
    boost_drop_rate_per_second = config.getfloat('Boost rise and fall speed', 'boost_drop_rate_per_second')
    boost_climb_rate_per_second = config.getfloat('Boost rise and fall speed', 'boost_climb_rate_per_second')
    COCKPIT_PIXELS = read_cockpit_pixels(icr2dash_ini_path)

    # Initialize the game state object
    gs = GameState()
    gs.boost_drop_rate_per_second = boost_drop_rate_per_second
    gs.boost_climb_rate_per_second = boost_climb_rate_per_second

    # Set up application context and overlay interface
    app = QApplication(sys.argv)
    cockpit_overlay = CockpitOverlay()

    # Create a timer to regularly update the game state and overlay
    timer = QTimer()
    timer.timeout.connect(update_loop)  # Connect the timer to the update loop function
    timer.start(16)  # Set the timer to trigger every 16 milliseconds (~60fps) for smooth updates

    # Start the Qt event loop, which handles GUI events and updates until the application exits
    sys.exit(app.exec_())