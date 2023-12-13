from PIL import ImageDraw
import configparser

def read_ini_to_numbers_and_rollbar(ini_file_path):
    config = configparser.ConfigParser()
    config.read(ini_file_path)

    numbers = []
    for section in config.sections():
        if section != 'Rollbar':
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

    return numbers, bars_x1, bars_x2, f_rollbar_y, r_rollbar_y, brake_y

# Define the coordinates for each segment of every number
ini_file_path = 'dash_reader.ini'
numbers, bars_x1, bars_x2, f_rollbar_y, r_rollbar_y, brake_y = read_ini_to_numbers_and_rollbar(ini_file_path)

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
            dash_plot.point((x,y),fill='red')

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

    seg_length = (bars_x2 - bars_x1)/8

    for segment in range(0, 9):
        f_rollbar_x = int(bars_x1 + seg_length * (segment+0.5))
        if not is_pixel_lit(pixels[f_rollbar_x, f_rollbar_y]):
            f_rollbar = segment - 1
            break

    for segment in range(0, 9):
        r_rollbar_x = int(bars_x1 + seg_length * (segment+0.5))
        if not is_pixel_lit(pixels[r_rollbar_x, r_rollbar_y]):
            r_rollbar = segment - 1
            break

    for segment in range(0, 9):
        brake_x = int(bars_x1 + seg_length * (segment+0.5))
        if not is_pixel_lit(pixels[brake_x, brake_y]):
            brake = segment - 1
            break

    return rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake
