"""
Dashboard Reader Module

This module provides functionality for reading and interpreting the in-game dashboard
displayed in a screenshot. It uses a configuration file (`dash_reader.ini`) to map pixel
locations for each dashboard element, enabling the program to extract values such as RPM,
boost, temperature, fuel level, speed, and gear.

Features:
- Reads pixel locations from a configuration file.
- Interprets LCD-style numbers and graphical elements (e.g., rollbars, boost knob).
- Returns dashboard values for use in other parts of the program.

Dependencies:
- configparser: For reading configuration files.
- PIL (Pillow): For image processing and drawing.
"""

import os
import sys
from PIL import ImageDraw
import configparser

def read_ini_to_numbers_and_rollbar(ini_file_path):
    """
    Reads the configuration file and extracts pixel locations for dashboard elements.

    Args:
        ini_file_path (str): Path to the INI configuration file.

    Returns:
        tuple: Contains:
            - numbers (list[dict]): List of dictionaries mapping LCD segments to pixel coordinates.
            - bars_x1 (int): X-coordinate of the start of the rollbar area.
            - bars_x2 (int): X-coordinate of the end of the rollbar area.
            - f_rollbar_y (int): Y-coordinate of the front rollbar.
            - r_rollbar_y (int): Y-coordinate of the rear rollbar.
            - brake_y (int): Y-coordinate of the brake bar.
            - boostxy (list[tuple]): List of pixel coordinates for the boost knob positions.

    Raises:
        ValueError: If the 'Rollbar' section is missing in the INI file.
    """
    
    config = configparser.ConfigParser()
    config.read(ini_file_path)

    numbers = []
    for section in config.sections():
        if section != 'Rollbar' and section != 'Boost knob':
            number_dict = {}
            for key, value in config.items(section):
                coords = tuple(map(int, value.split(',')))
                number_dict[key] = coords
            numbers.append(number_dict)

    # Separate handling for the 'Rollbar' section
    if 'Rollbar' in config.sections():
        bars_x1 = int(config.get('Rollbar', 'Bars_min_x'))
        bars_x2 = int(config.get('Rollbar', 'Bars_max_x'))
        f_rollbar_y = int(config.get('Rollbar', 'Front_rollbar_y'))
        r_rollbar_y = int(config.get('Rollbar', 'Rear_rollbar_y'))
        brake_y = int(config.get('Rollbar', 'Brake_y'))
    else:
        raise ValueError("Rollbar section is missing in the INI file.")

    # Boost knob
    boost1_x, boost1_y = tuple(map(int, config.get('Boost knob', 'Boost_knob_1').split(',')))
    boost2_x, boost2_y = tuple(map(int, config.get('Boost knob', 'Boost_knob_2').split(',')))
    boost3_x, boost3_y = tuple(map(int, config.get('Boost knob', 'Boost_knob_3').split(',')))
    boost4_x, boost4_y = tuple(map(int, config.get('Boost knob', 'Boost_knob_4').split(',')))
    boost5_x, boost5_y = tuple(map(int, config.get('Boost knob', 'Boost_knob_5').split(',')))
    boost6_x, boost6_y = tuple(map(int, config.get('Boost knob', 'Boost_knob_6').split(',')))
    boost7_x, boost7_y = tuple(map(int, config.get('Boost knob', 'Boost_knob_7').split(',')))
    boost8_x, boost8_y = tuple(map(int, config.get('Boost knob', 'Boost_knob_8').split(',')))
    boost9_x, boost9_y = tuple(map(int, config.get('Boost knob', 'Boost_knob_9').split(',')))

    boostxy = [(boost1_x, boost1_y),
               (boost2_x, boost2_y),
               (boost3_x, boost3_y),
               (boost4_x, boost4_y),
               (boost5_x, boost5_y),
               (boost6_x, boost6_y),
               (boost7_x, boost7_y),
               (boost8_x, boost8_y),
               (boost9_x, boost9_y),
               ]

    return numbers, bars_x1, bars_x2, f_rollbar_y, r_rollbar_y, brake_y, boostxy

# Define the coordinates for each segment of every number
ini_file_path = "dash_reader.ini"
print(f"Looking for dashboard reader config file at: {os.path.abspath(ini_file_path)}")
if not os.path.exists(ini_file_path):
    print("Configuration file not found!")
    sys.exit(1)

numbers, bars_x1, bars_x2, f_rollbar_y, r_rollbar_y, brake_y, boostxy = read_ini_to_numbers_and_rollbar(ini_file_path)

LCD_NUMBERS = {
    frozenset(['a', 'b', 'c', 'd', 'e', 'f']): '0',
    frozenset(['b', 'c']): '1',
    frozenset(['a', 'b', 'g', 'e', 'd']): '2',
    frozenset(['a', 'b', 'g', 'c', 'd']): '3',
    frozenset(['f', 'g', 'b', 'c']): '4',
    frozenset(['a', 'f', 'g', 'c', 'd']): '5',
    frozenset(['a', 'f', 'g', 'e', 'c', 'd']): '6',
    frozenset(['a', 'b', 'c']): '7',
    frozenset(['a', 'b', 'c', 'd', 'e', 'f', 'g']): '8',
    frozenset(['a', 'b', 'c', 'd', 'f', 'g']): '9'
}

def is_pixel_lit(pixel, threshold):
    """
    Determines if a pixel is considered 'lit' based on its brightness.

    Args:
        pixel (tuple): RGB tuple representing the pixel.
        threshold (int): Brightness threshold (lower values are 'lit').

    Returns:
        bool: True if the pixel is lit, False otherwise.
    """
    r, g, b = pixel
    brightness = (r + g + b) / 3
    return brightness < threshold

def plot_lcd_locations(cropped_screenshot):
    """
    Visualizes LCD segment locations by marking them on the provided image.

    Args:
        cropped_screenshot (PIL.Image.Image): The cropped screenshot image.

    Returns:
        PIL.Image.Image: The annotated image.
    """
    dash_plot = ImageDraw.Draw(cropped_screenshot)
    for number in numbers:
        coords = [coord for coord in number.values()]
        for x, y in coords:
            dash_plot.point((x, y), fill='red')

    return cropped_screenshot

def read_dashboard(cropped_screenshot, threshold):
    """
    Reads dashboard values from a cropped screenshot image.

    Args:
        cropped_screenshot (PIL.Image.Image): The cropped screenshot of the dashboard.
        threshold (int): Brightness threshold for detecting lit pixels.

    Returns:
        tuple: Contains:
            - rpm (int): RPM value.
            - boost (int): Boost value.
            - temp (int): Temperature value.
            - fuel (float): Fuel level.
            - mph (int): Speed in mph.
            - gear (int): Current gear.
            - f_rollbar (int): Front rollbar position (0-8).
            - r_rollbar (int): Rear rollbar position (0-8).
            - brake (int): Brake position (0-8).
            - boost_knob (int): Boost knob position (1-9).
            - laptime (float): Lap time in seconds.
    """
    pixels = cropped_screenshot.load()

    readout = []

    for number in numbers:
        active_segments = []

        for segment, coord in number.items():
            if is_pixel_lit(pixels[coord[0], coord[1]], threshold):
                active_segments.append(segment)

        number_identified = LCD_NUMBERS.get(frozenset(active_segments))
        if number_identified:
            readout.append(int(number_identified))
        else:
            readout.append(0)  # Placeholder for unidentified numbers

    # Extract the RPM value from the first 4 LCD digits
    rpm = readout[3] * 1 + readout[2] * 10 + readout[1] * 100 + readout[0] * 1000

    # Extract the boost value from the next 2 LCD digits
    boost = readout[4] * 10 + readout[5] * 1

    # Extract the temperature value from the next 3 LCD digits
    temp = readout[6] * 100 + readout[7] * 10 + readout[8] * 1
    
    # Extract the fuel value as a float (3 digits and 2 decimals)
    fuel = readout[9] * 10 + readout[10] * 1 + readout[11] * .1 + readout[12] * .01

    # Extract the speed from the next 3 LCD digits
    mph = readout[13] * 100 + readout[14] * 10 + readout[15] * 1

    # Extract the current gear from the LCD digit at position 16
    gear = readout[16]

    # Calculate the lap time in seconds
    # The digits at positions 22, 21, and 20 represent the minutes, tens of seconds, and single seconds respectively.
    # Digits at positions 19, 18, and 17 represent the tenths, hundredths, and thousandths of a second.
    laptime = readout[22] * 60 + readout[21] * 10 + readout[20] + readout[19] * 0.1 + readout[18] * 0.01 + readout[17] * 0.001

    seg_length = (bars_x2 - bars_x1) / 8

    f_rollbar = r_rollbar = brake = 0  # Initialize variables

    for segment in range(0, 9):
        f_rollbar_x = int(bars_x1 + seg_length * (segment + 0.5))
        if not is_pixel_lit(pixels[f_rollbar_x, f_rollbar_y], threshold):
            f_rollbar = segment - 1
            break

    for segment in range(0, 9):
        r_rollbar_x = int(bars_x1 + seg_length * (segment + 0.5))
        if not is_pixel_lit(pixels[r_rollbar_x, r_rollbar_y], threshold):
            r_rollbar = segment - 1
            break

    for segment in range(0, 9):
        brake_x = int(bars_x1 + seg_length * (segment + 0.5))
        if not is_pixel_lit(pixels[brake_x, brake_y], threshold):
            brake = segment - 1
            break

    for boost_pos in range(0,9):
        if is_pixel_lit(pixels[boostxy[boost_pos][0], boostxy[boost_pos][1]], threshold):
            boost_knob = boost_pos + 1
            break

    return rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake, boost_knob, laptime
