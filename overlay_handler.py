import win32gui
#from datetime import datetime
from window_capture import find_dosbox_window, capture_window, get_title_bar_height
from image_processing import crop_black_borders_with_coords, is_in_cockpit_view
from dashboard_reader import read_dashboard, plot_lcd_locations
from PyQt5.QtWidgets import QApplication
from overlay import CockpitOverlay  # Import the CockpitOverlay class
import threading
from gear_handler import GearHandler
import keyboard

class OverlayHandler:
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

    def lock_overlay(self):
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
        """Set up the overlay interface."""
        self.app = app
        self.cockpit_overlay = CockpitOverlay()  # Initialize the CockpitOverlay
    
    def update_loop(self):
        """Main loop for updating the overlay and handling user inputs."""
        hwnd = find_dosbox_window()
    
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
        """Manages overlay updates in sync with DOSBox window state."""
        # Validate window handle and update overlay
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd) and hwnd == win32gui.GetForegroundWindow():
            self.last_screenshot = capture_window(hwnd)

            cropped_screenshot, coords = crop_black_borders_with_coords(self.last_screenshot, self.cropbox)

            if is_in_cockpit_view(cropped_screenshot, self.cockpit_pixels) and self.cockpit_on:
                # Read dashboard data
                rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake, boost_knob = read_dashboard(cropped_screenshot)
                self.gs.update(rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake, boost_knob)
                self.cockpit_overlay.setGauges(self.gs.rpm, self.gs.cur_boost, self.gs.temp, self.gs.fuel, self.gs.mph, self.gs.gear, self.gs.f_rollbar, self.gs.r_rollbar, self.gs.brake, self.gs.boost_knob)
                self.cockpit_overlay.show()
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
        if self.last_screenshot is not None:
            cropped_screenshot, _ = crop_black_borders_with_coords(self.last_screenshot)
            plot = plot_lcd_locations(cropped_screenshot)
            screenshot_path = f'screenshot.png'
            plot.save(screenshot_path)
            print(f'Screenshot saved as {screenshot_path}')