import sys
import configparser
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import os

from game_state import GameState
from overlay_handler import OverlayHandler
from utils import read_cockpit_pixels, play_gear_grinding_sound, stop_gear_grinding_sound

def main():
    print('ICR2 cockpit overlay script started - v2.0')
    print('Configurations can be edited in icr2dash.ini, overlay.ini and dash_reader.ini')
    print('Leave this program running in the background when you run ICR2 in DOSBox')
    print('Once you are in ICR2:')
    print('   Ctrl-S to take a screenshot with LCD reading points.')
    print('   Ctrl-L to lock the DOSBox window location (prevents errors in black tunnels)')

    # Initialize global variables
    config_path = 'icr2dash.ini'
    print(f"Loading config file at: {os.path.abspath(config_path)}")
    
    if not os.path.exists(config_path):
        print("Configuration file not found!")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path)

    gs = GameState()
    cockpit_pixels = read_cockpit_pixels(config_path)

    overlay_handler = OverlayHandler(gs, cockpit_pixels, config)
    
    # Set up application context and overlay interface
    app = QApplication(sys.argv)
    overlay_handler.setup_overlay(app)

    
    # Create a timer to regularly update the game state and overlay
    timer = QTimer()
    timer.timeout.connect(overlay_handler.update_loop)  # Connect the timer to the update loop function
    timer.start(config.getint('General', 'loop_ms'))  # Set the timer to trigger every 16 milliseconds (~60fps) for smooth updates

    print ('ICR2dash has finished loading, now waiting for ICR2 to start')

    # Start the Qt event loop, which handles GUI events and updates until the application exits
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
