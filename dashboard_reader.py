import os
import sys
from PIL import ImageDraw
import configparser

def read_ini_to_numbers_and_rollbar(ini_file_path):
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

def is_pixel_lit(pixel, threshold=128):
    """Check if a pixel is 'lit' (dark in this case) based on a threshold."""
    r, g, b = pixel
    brightness = (r + g + b) / 3
    return brightness < threshold

def plot_lcd_locations(cropped_screenshot):
    """Plots where the LCD locations are and returns a new PIL image"""
    dash_plot = ImageDraw.Draw(cropped_screenshot)
    for number in numbers:
        coords = [coord for coord in number.values()]
        for x, y in coords:
            dash_plot.point((x, y), fill='red')

    return cropped_screenshot

def read_dashboard(cropped_screenshot):
    """Read the numbers from the screenshot using the numbers list."""
    pixels = cropped_screenshot.load()

    readout = []

    for number in numbers:
        active_segments = []

        for segment, coord in number.items():
            if is_pixel_lit(pixels[coord[0], coord[1]]):
                active_segments.append(segment)

        number_identified = LCD_NUMBERS.get(frozenset(active_segments))
        if number_identified:
            readout.append(int(number_identified))
        else:
            readout.append(0)  # Placeholder for unidentified numbers

    rpm = readout[3] * 1 + readout[2] * 10 + readout[1] * 100 + readout[0] * 1000
    boost = readout[4] * 10 + readout[5] * 1
    temp = readout[6] * 100 + readout[7] * 10 + readout[8] * 1
    fuel = readout[9] * 10 + readout[10] * 1 + readout[11] * .1 + readout[12] * .01
    mph = readout[13] * 100 + readout[14] * 10 + readout[15] * 1
    gear = readout[16]

    seg_length = (bars_x2 - bars_x1) / 8

    f_rollbar = r_rollbar = brake = 0  # Initialize variables

    for segment in range(0, 9):
        f_rollbar_x = int(bars_x1 + seg_length * (segment + 0.5))
        if not is_pixel_lit(pixels[f_rollbar_x, f_rollbar_y]):
            f_rollbar = segment - 1
            break

    for segment in range(0, 9):
        r_rollbar_x = int(bars_x1 + seg_length * (segment + 0.5))
        if not is_pixel_lit(pixels[r_rollbar_x, r_rollbar_y]):
            r_rollbar = segment - 1
            break

    for segment in range(0, 9):
        brake_x = int(bars_x1 + seg_length * (segment + 0.5))
        if not is_pixel_lit(pixels[brake_x, brake_y]):
            brake = segment - 1
            break

    for boost_pos in range(0,9):
        if is_pixel_lit(pixels[boostxy[boost_pos][0], boostxy[boost_pos][1]]):
            boost_knob = boost_pos + 1
            break

    #print (rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake, boost_knob)

    return rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake, boost_knob
