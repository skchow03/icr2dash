"""
OverlayHandler Module

This module defines the `OverlayHandler` class, which manages the overlay interface for the ICR2 racing game.
It handles:
- Capturing the DOSBox window.
- Processing the game state using pixel data and configurations.
- Displaying the overlay using PyQt5.
- Managing user interactions, such as locking the overlay position or handling gear changes.

Classes:
- OverlayHandler: Manages the overlay, game state, and user interactions.

Dependencies:
- win32gui: For interacting with the DOSBox window.
- Custom modules: `window_capture`, `image_processing`, `dashboard_reader`, `overlay`, `gear_handler`, and `laptime`.

Usage:
1. Instantiate the `OverlayHandler` with game state, cockpit pixel data, and configuration.
2. Call `setup_overlay(app)` to initialize the PyQt5 application.
3. Use `update_loop()` as the main method to synchronize overlay updates with the game state.
"""

import win32gui
from window_capture import find_dosbox_window, capture_window, get_title_bar_height
from image_processing import crop_black_borders_with_coords, is_in_cockpit_view
from dashboard_reader import read_dashboard, plot_lcd_locations
from overlay import CockpitOverlay
import threading
from gear_handler import GearHandler
import keyboard
from telemetry import telemetry

class OverlayHandler:
    """
    OverlayHandler Class

    Handles the main logic for managing the ICR2 overlay interface. This includes:
    - Capturing the DOSBox window and processing pixel data.
    - Updating the game state based on dashboard readings.
    - Displaying and positioning the overlay relative to the DOSBox window.
    - Managing user input, such as locking the overlay position or starting/stopping the gear listener thread.

    Attributes:
        gs (GameState): Represents the current state of the game.
        cockpit_pixels (dict): Pixel data for detecting cockpit elements.
        config (ConfigParser): Configuration settings for the overlay.
        gear_handler (GearHandler): Handles gear-related logic and threading.
        laps (laptimes): Tracks lap times and fuel usage.
        cockpit_overlay (CockpitOverlay): The GUI overlay instance.
    """

    def __init__(self, game_state, cockpit_pixels, config):
        self.gs = game_state
        self.cockpit_pixels = cockpit_pixels
        self.config = config

        self.last_screenshot = None
        self.dosbox_window_opened = False
        self.x_adjustment = config.getint('Overlay positioning', 'x_adjustment')
        self.y_adjustment = config.getint('Overlay positioning', 'y_adjustment')
        self.boost_drop_rate_per_second = config.getfloat('Boost rise and fall speed', 'boost_drop_rate_per_second')
        self.boost_climb_rate_per_second = config.getfloat('Boost rise and fall speed', 'boost_climb_rate_per_second')
        self.cockpit_on = True
        self.overlay_locked = False
        self.cropbox = None
        self.hshifter_on = config.get('Gear shifting', 'hshifter').lower() == 'on'
        self.lcd_threshold = config.getint('General', 'lcd_detect_threshold')
        self.cockpit_visible = True

        self.last_speed = 0
        self.last_color = 'green'

        self.app_keywords = [
            keyword.strip().upper() 
            for keyword in config.get('General', 'app_keywords').split(',')
            ]
        print (f'Watching for window with following keywords: {self.app_keywords}')
        
        # Initialize the game state object
        self.gs.boost_drop_rate_per_second = self.boost_drop_rate_per_second
        self.gs.boost_climb_rate_per_second = self.boost_climb_rate_per_second

        # Initialize the gear handler
        self.gear_handler = GearHandler(self.gs, config, self)
        self.stop_event = threading.Event()
        self.gear_listener_thread = threading.Thread(target=self.gear_handler.gear_change_listener, args=(self.gs, self.stop_event), daemon=True)

        # Set up the keyboard hotkey
        keyboard.add_hotkey('ctrl+s', self.take_screenshot)
        keyboard.add_hotkey('ctrl+l', self.lock_overlay)
        #keyboard.add_hotkey('ctrl+t', self.reset_telemetry)
        keyboard.add_hotkey('ctrl+o', self.toggle_overlay)

        # Initialize laptime object
        #self.telemetry = telemetry()

    def toggle_overlay(self):
        if self.cockpit_visible:
            self.cockpit_visible = False
            print ('Toggle cockpit off')
        else:
            self.cockpit_visible = True
            print ('Toggle cockpit on')

    def reset_telemetry(self):
        self.telemetry.reset()

    def lock_overlay(self):
        """
        Lock or unlock the overlay position.

        When locked, the overlay remains in a fixed position relative to the
        DOSBox window. When unlocked, the position adjusts dynamically based on
        the window's location and size.
        """
        if self.overlay_locked:
            self.overlay_locked = False
            self.cropbox = None
            print ('Overlay position unlocked')
        else:
            self.overlay_locked = True
            _, self.cropbox = crop_black_borders_with_coords(self.last_screenshot, None)
            print (f'Overlay position locked with cropping box at {self.cropbox}')

    def start_gear_listener(self):
        """Start the gear listener thread if it's not already running."""
        if self.gear_listener_thread is None or not self.gear_listener_thread.is_alive():
            self.stop_event.clear()
            self.gear_listener_thread = threading.Thread(target=self.gear_handler.gear_change_listener, args=(self.gs, self.stop_event), daemon=True)
            self.gear_listener_thread.start()
            #print (f'Starting gear listener thread')

    def stop_gear_listener(self):
        """Stop the gear listener thread if it's running."""
        if self.gear_listener_thread is not None and self.gear_listener_thread.is_alive():
            self.stop_event.set()
            self.gear_listener_thread.join()
            self.gear_listener_thread = None
            #print (f'Stopping gear listener thread')

    def setup_overlay(self, app):
        """
        Initialize the PyQt5 overlay interface.

        Args:
            app (QApplication): The PyQt5 application instance.
        """
        self.app = app
        self.cockpit_overlay = CockpitOverlay()  # Initialize the CockpitOverlay
    
    def update_loop(self):
        """
        Main update loop for the overlay.

        Checks for the presence of the DOSBox window, updates the overlay's
        position and data if the game is running, and manages user inputs.
        If the DOSBox window is not found, the application exits.
        """
        hwnd = find_dosbox_window(self.app_keywords)
    
        # Ensure DOSBox window is present and handle overlay accordingly
        if hwnd:
            if not self.dosbox_window_opened:
                self.dosbox_window_opened = True
                print('ICR2 DOSBox window detected')
            self.handle_dosbox_overlay(hwnd)
        else:
            if self.dosbox_window_opened:
                print('Script ending')
                self.cockpit_overlay.hide()  # Hide overlay if DOSBox window is missing
                self.app.quit()  # Quit the application
            self.cockpit_overlay.hide()  # Hide overlay if DOSBox window is missing
            self.stop_gear_listener()  # Stop the gear listener thread

    def handle_dosbox_overlay(self, hwnd):
        """
        Update the overlay in sync with the DOSBox window state.

        Args:
            hwnd (int): Handle to the DOSBox window.
        """
        # Validate window handle and update overlay
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd) and hwnd == win32gui.GetForegroundWindow():
            self.last_screenshot = capture_window(hwnd)

            cropped_screenshot, coords = crop_black_borders_with_coords(self.last_screenshot, self.cropbox)

            if is_in_cockpit_view(cropped_screenshot, self.cockpit_pixels) and self.cockpit_on:
                # Read dashboard data
                rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake, boost_knob, laptime = read_dashboard(cropped_screenshot, self.lcd_threshold)
#                print (laptime)
                self.gs.update(rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake, boost_knob, laptime)

                #self.telemetry.update(laptime, fuel)

                self.cockpit_overlay.setGauges(self.gs.rpm, self.gs.cur_boost, self.gs.temp, self.gs.fuel, self.gs.mph, self.gs.gear, self.gs.f_rollbar, self.gs.r_rollbar, self.gs.brake, self.gs.boost_knob)

                # Handle HUD
                # speed_diff = mph - self.last_speed
                # if speed_diff > 0:
                #     color = 'green'
                #     self.last_color = 'green'
                # elif speed_diff < 0:
                #     color = 'red'
                #     self.last_color = 'red'
                # else:
                #     color = self.last_color
                # self.last_speed = mph
                # self.cockpit_overlay.clear_hud_text()
                # self.cockpit_overlay.add_hud_text(str(mph),0.5,0.5,color)
                


                if self.cockpit_visible:
                    self.cockpit_overlay.show()
                else:
                    self.cockpit_overlay.hide()


                if self.hshifter_on:            
                   self.start_gear_listener()  # Start the gear listener thread

            else:
                self.cockpit_overlay.hide()
                if self.hshifter_on:
                    self.stop_gear_listener()  # Stop the gear listener thread
    
            win_rect = win32gui.GetWindowRect(hwnd)
            win_x, win_y = win_rect[0], win_rect[1]
            title_bar_height = get_title_bar_height(hwnd)
    
            if not self.overlay_locked:
                self.cockpit_overlay.setPositionAndSize(
                    coords[0] + win_x + self.x_adjustment, 
                    coords[1] + win_y + title_bar_height + self.y_adjustment, 
                    coords[2] - coords[0], 
                    coords[3] - coords[1]
                )

            self.cockpit_overlay.update()
        else:
            self.cockpit_overlay.hide()
            if self.hshifter_on:
                self.stop_gear_listener()  # Stop the gear listener thread


    def take_screenshot(self):
        """Take a screenshot of the cropped_screenshot without the overlay."""

        hwnd = find_dosbox_window(self.app_keywords)
        self.last_screenshot = capture_window(hwnd)

        if self.last_screenshot is not None:
            cropped_screenshot, _ = crop_black_borders_with_coords(self.last_screenshot)
            plot = plot_lcd_locations(cropped_screenshot)
            screenshot_path = f'screenshot.png'
            plot.save(screenshot_path)
            print(f'Screenshot saved as {screenshot_path}')
