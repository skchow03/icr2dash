"""
ICR2 Cockpit Overlay Script

This script initializes and manages an overlay interface for the ICR2 racing game when run in DOSBox.
It uses a PyQt5-based GUI for rendering the overlay and regularly updates the state based on
configuration files and screen pixel readings.

Modules and Functions:
- GameState: Tracks the state of the game and interacts with the overlay.
- OverlayHandler: Handles GUI overlay logic and updates.
- Utility functions: Read cockpit pixels, play/stop sound effects.

Usage:
1. Ensure the necessary configuration files (`icr2dash.ini`, `overlay.ini`, `dash_reader.ini`) are set up correctly.
2. Run this script before starting ICR2 in DOSBox.
3. Follow the on-screen instructions to capture the cockpit points and lock the window.

Dependencies:
- PyQt5: For GUI elements and application loop.
- ConfigParser: For reading configuration files.
- Custom modules: `game_state`, `overlay_handler`, and `utils`.

Author: SK Chow
Version: 3.4
"""

import sys
import configparser
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import os

from game_state import GameState
from overlay_handler import OverlayHandler
from utils import read_cockpit_pixels, play_gear_grinding_sound, stop_gear_grinding_sound

def main():
    """
    Entry point for the ICR2 cockpit overlay script.

    This function initializes the overlay system, loads configurations, sets up the game state,
    and starts the PyQt5 application loop to manage the overlay.

    Steps:
    1. Prints startup instructions and loads configuration files.
    2. Initializes the game state, overlay handler, and cockpit pixel mappings.
    3. Sets up a QTimer for regular updates and starts the PyQt5 event loop.

    Raises:
        SystemExit: If the configuration file is missing or the PyQt5 application exits.
    """

    # Print startup information and user instructions
    print('ICR2 cockpit overlay script started - v3.4')
    print('Configurations can be edited in icr2dash.ini, overlay.ini and dash_reader.ini')
    print('Leave this program running in the background when you run ICR2 in DOSBox or Windy')
    print('Once you are in ICR2:')
    print('   Ctrl-S to take a screenshot with LCD reading points.')
    print('   Ctrl-L to lock the window location (prevents errors in black tunnels)')
    print('   Ctrl-O to toggle cockpit overlay on/off')

    # Load configuration file and validate its existence
    config_path = 'icr2dash.ini'
    print(f"Loading config file at: {os.path.abspath(config_path)}")
    
    if not os.path.exists(config_path):
        print("Configuration file neot found!")
        sys.exit(1)

    # Read configuration settings
    config = configparser.ConfigParser()
    config.read(config_path)

    # Initialize the game state, cockpit pixel mappings, and overlay handler
    gs = GameState()
    cockpit_pixels = read_cockpit_pixels(config_path)
    overlay_handler = OverlayHandler(gs, cockpit_pixels, config)
    
    # Set up the PyQt5 application and overlay
    app = QApplication(sys.argv)
    overlay_handler.setup_overlay(app)

    # Start a timer to update the game state and overlay at a fixed interval
    timer = QTimer()
    timer.timeout.connect(overlay_handler.update_loop)  # Call the update loop regularly
    timer.start(config.getint('General', 'loop_ms'))  # Trigger updates based on config (e.g., ~60 FPS)

    print ('ICR2dash has finished loading, now waiting for ICR2 to start')

    # Start the Qt event loop, which handles GUI events and updates until the application exits
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
