import configparser
import pygame

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

def play_gear_grinding_sound(gear_grinding_channel, gear_grinding_sound):
    """Play the gear grinding sound."""
    if not gear_grinding_channel.get_busy():
        gear_grinding_channel.play(gear_grinding_sound)

def stop_gear_grinding_sound(gear_grinding_channel):
    """Stop the gear grinding sound."""
    if gear_grinding_channel:
        gear_grinding_channel.stop()
