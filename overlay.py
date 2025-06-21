"""
CockpitOverlay Module

This module provides a visual overlay for the ICR2 racing game, displaying various gauges and indicators.
It uses PyQt5 for rendering and integrates configuration settings to adjust the layout and behavior.

Classes:
- Gauge: Represents a single gauge with a rotating needle.
- CockpitOverlay: Manages the main overlay window and draws gauges, lights, and other visual elements.

Usage:
1. Initialize the `CockpitOverlay` instance and load configuration settings.
2. Use `setGauges` to update gauge values dynamically.
3. Use the `paintEvent` method to render the overlay.

Dependencies:
- PyQt5: For GUI rendering and widget management.
- PIL: For image manipulation.
- ConfigParser: For reading configuration files.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPixmap, QTransform, QFont
from PyQt5.QtCore import Qt
from PIL import Image
import time
import os
import configparser
import sys

class Gauge:
    """
    Represents a single gauge with a rotating needle.

    Attributes:
        needle_image (QPixmap): The image of the needle.
        pivot (tuple): The (x, y) pivot point for rotation.
        min_value (int): The minimum value of the gauge.
        max_value (int): The maximum value of the gauge.
        gauge_center (tuple): The (x, y) center of the gauge.
        section_one_end (int): End value of the first section of the gauge.
        section_two_start (int): Start value of the second section of the gauge.
        min_angle (float): The minimum angle of the needle.
        max_angle_section_one (float): Maximum angle for section one.
        max_angle_section_two (float): Maximum angle for section two.
    """
    def __init__(self, needle_image_path, pivot, min_value, max_value, gauge_center,
                 section_one_end, section_two_start, min_angle, max_angle_section_one, max_angle_section_two):
        self.needle_image = QPixmap(needle_image_path)
        if self.needle_image.isNull():
            print(f"Failed to load needle image from {needle_image_path}")
        self.pivot = pivot
        self.min_value = min_value
        self.max_value = max_value
        self.gauge_center = gauge_center
        self.section_one_end = section_one_end
        self.section_two_start = section_two_start
        self.min_angle = min_angle
        self.max_angle_section_one = max_angle_section_one
        self.max_angle_section_two = max_angle_section_two




    def rotate_needle(self, value):
        """
        Rotates the needle based on the input value.

        Args:
            value (float): The current value of the gauge.
        
        Returns:
            QPixmap: Transformed needle image based on rotation.
        """
        if value <= self.section_one_end:
            angle_range = self.max_angle_section_one - self.min_angle
            value_range = self.section_one_end - self.min_value
            angle = ((value - self.min_value) / value_range) * angle_range + self.min_angle
        else:
            angle_range = self.max_angle_section_two - self.max_angle_section_one
            value_range = self.max_value - self.section_two_start
            angle = ((value - self.section_two_start) / value_range) * angle_range + self.max_angle_section_one

        transform = QTransform().translate(self.pivot[0], self.pivot[1]).rotate(-angle).translate(-self.pivot[0], -self.pivot[1])
        return self.needle_image.transformed(transform)



class CockpitOverlay(QWidget):
    """
    Manages the main overlay window and renders gauges, indicators, and lights.

    Attributes:
        image (QPixmap): The base cockpit image.
        tachometer_gauge (Gauge): RPM gauge.
        boost_gauge (Gauge): Boost gauge.
        temp_gauge (Gauge): Temperature gauge.
        fuel_gauge (Gauge): Fuel gauge.
        brakebias_knob (Gauge): Brake bias knob.
        boost_knob (Gauge): Boost knob.
        rpm (int): Current RPM value.
        boost (float): Current boost value.
        temp (float): Current temperature value.
        fuel (float): Current fuel value.
        mph (int): Current speed in mph.
        gear (int): Current gear.
    """

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)


        config_path = 'overlay.ini'
        print(f"Loading overlay config file at: {os.path.abspath(config_path)}")
        
        if not os.path.exists(config_path):
            print("Configuration file not found!")
            sys.exit(1)

        config = configparser.ConfigParser()
        config.read(config_path)

        self.image = QPixmap(config.get('General', 'cockpit_path'))

        self.tachometer_gauge = self.create_gauge(config, "Tachometer")
        self.boost_gauge = self.create_gauge(config, "Boost")
        self.temp_gauge = self.create_gauge(config, "Temperature")
        self.fuel_gauge = self.create_gauge(config, "Fuel")
        self.brakebias_knob = self.create_gauge(config, "Brake bias")
        self.boost_knob = self.create_gauge(config, "Boost knob")

        self.rpm = 0
        self.boost = 0
        self.temp = 0
        self.fuel = 0
        self.mph = 0
        self.rpm_threshold = int(config.get('General', 'high_rpm'))
        self.high_temp = int(config.get('General', 'high_temp'))
        self.critical_fuel = int(config.get('General', 'critical_fuel'))
        self.low_fuel = int(config.get('General', 'low_fuel'))
        self.fuel_blinker = False
        self.blink_timer = 0
        self.blink_duration = 0.5
        self.last_blink_time = 0
        self.boost_setting = 1

        self.fuel_x, self.fuel_y = tuple(map(int, config.get('General', 'fuellight').split(',')))
        self.temp_x, self.temp_y = tuple(map(int, config.get('General', 'templight').split(',')))
        self.rpm_x, self.rpm_y = tuple(map(int, config.get('General', 'rpmlight').split(',')))


        self.temp_blinker = False
        self.temp_blink_timer = 0
        self.temp_blink_duration = 0.5
        self.temp_last_blink_time = 0

        image_pixmap = QPixmap(config.get('LCD display', 'lcdnums_path'))
        self.lcd_speed1_x, self.lcd_speed1_y = tuple(map(int, config.get('LCD display', 'lcd_speed1').split(',')))
        self.lcd_speed2_x, self.lcd_speed2_y = tuple(map(int, config.get('LCD display', 'lcd_speed2').split(',')))
        self.lcd_speed3_x, self.lcd_speed3_y = tuple(map(int, config.get('LCD display', 'lcd_speed3').split(',')))
        self.lcd_gear_x, self.lcd_gear_y = tuple(map(int, config.get('LCD display', 'lcd_gear').split(',')))
        
        digit_width = image_pixmap.width() // 10
        digit_height = image_pixmap.height()

        self.digit_images = []
        for i in range(10):
            x = i * digit_width
            y = 0
            digit_pixmap = image_pixmap.copy(x, y, digit_width, digit_height)
            self.digit_images.append(digit_pixmap)

        self.rollbar_images = [
            QPixmap(config.get('Rollbars', 'rollbar1')),
            QPixmap(config.get('Rollbars', 'rollbar2')),
            QPixmap(config.get('Rollbars', 'rollbar3')),
            QPixmap(config.get('Rollbars', 'rollbar4')),
            QPixmap(config.get('Rollbars', 'rollbar5')),
            QPixmap(config.get('Rollbars', 'rollbar6')),
            QPixmap(config.get('Rollbars', 'rollbar7')),
            QPixmap(config.get('Rollbars', 'rollbar8'))
        ]

        self.fbar_x, self.fbar_y = tuple(map(int, config.get('Rollbars', 'front_rollbar').split(',')))
        self.rbar_x, self.rbar_y = tuple(map(int, config.get('Rollbars', 'rear_rollbar').split(',')))
        self.shifter_x, self.shifter_y = tuple(map(int, config.get('Shifter', 'shifter').split(',')))

        self.gear_images = [
            QPixmap(config.get('Shifter', 'gear1')),
            QPixmap(config.get('Shifter', 'gear2')),
            QPixmap(config.get('Shifter', 'gear3')),
            QPixmap(config.get('Shifter', 'gear4')),
            QPixmap(config.get('Shifter', 'gear5')),
            QPixmap(config.get('Shifter', 'gear6')),
        ]

        self.rpmlight = QPixmap(config.get('General', 'rpmlight_path'))
        self.fuellight = QPixmap(config.get('General', 'fuellight_path'))

        # HUD Text Elements: [(text, x, y)]
        self.hud_texts = []

    def add_hud_text(self, text, x_ratio, y_ratio, color):
        """
        Adds a HUD text element using **relative positioning**.

        Args:
            text (str): The text to display.
            x_ratio (float): Relative X position (0.0 = left, 1.0 = right).
            y_ratio (float): Relative Y position (0.0 = top, 1.0 = bottom).
        """
        self.hud_texts.append((text, x_ratio, y_ratio, color))
        self.update()  # Trigger a repaint

    def clear_hud_text(self):
        """
        Clears all HUD text elements from the overlay.
        """
        self.hud_texts = []
        self.update()  # Trigger a repaint


    def create_gauge(self, config, section):
        """
        Creates a Gauge instance based on configuration settings.

        Args:
            config (ConfigParser): Configuration object with gauge settings.
            section (str): The section name in the configuration file.

        Returns:
            Gauge: Configured Gauge instance.
        """

        needle_image_path = config.get(section, 'needle_image_path')
        pivot = tuple(map(int, config.get(section, 'pivot').split(',')))
        min_value = config.getint(section, 'min_value')
        max_value = config.getint(section, 'max_value')
        gauge_center = tuple(map(int, config.get(section, 'gauge_center').split(',')))
        section_one_end = config.getint(section, 'section_one_end')
        section_two_start = config.getint(section, 'section_two_start')
        min_angle = config.getfloat(section, 'min_angle')
        max_angle_section_one = config.getfloat(section, 'max_angle_section_one')
        max_angle_section_two = config.getfloat(section, 'max_angle_section_two')

        return Gauge(
            needle_image_path=needle_image_path,
            pivot=pivot,
            min_value=min_value,
            max_value=max_value,
            gauge_center=gauge_center,
            section_one_end=section_one_end,
            section_two_start=section_two_start,
            min_angle=min_angle,
            max_angle_section_one=max_angle_section_one,
            max_angle_section_two=max_angle_section_two
        ) 

    def setPositionAndSize(self, x, y, width, height):
        self.setGeometry(x, y, width, height)

    def setGauges(self, rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake, boost_setting):
        """
        Updates gauge values and triggers a repaint of the overlay.

        Args:
            rpm (int): RPM value.
            boost (float): Boost value.
            temp (float): Temperature value.
            fuel (float): Fuel value.
            mph (int): Speed in mph.
            gear (int): Current gear.
            f_rollbar (int): Front rollbar setting.
            r_rollbar (int): Rear rollbar setting.
            brake (float): Brake bias value.
            boost_setting (int): Boost knob setting.
        """       
        self.rpm = rpm
        self.boost = boost
        self.temp = temp
        self.fuel = fuel
        self.mph = mph
        self.gear = gear
        self.f_rollbar = f_rollbar
        self.r_rollbar = r_rollbar
        self.brake = brake
        self.boost_setting = boost_setting
        self.update()

    def paintEvent(self, event):
        """
        Handles rendering of the overlay.

        Draws the base cockpit image, updates gauge positions and rotations,
        and renders lights and other indicators based on the current state.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        combined_image = self.image.copy()


        rotated_tachneedle = self.tachometer_gauge.rotate_needle(self.rpm)
        rotated_boostneedle = self.boost_gauge.rotate_needle(self.boost)
        rotated_tempneedle = self.temp_gauge.rotate_needle(self.temp)
        rotated_fuelneedle = self.fuel_gauge.rotate_needle(self.fuel)
        rotated_brakebias = self.brakebias_knob.rotate_needle(self.brake)
        rotated_boostknob = self.boost_knob.rotate_needle(self.boost_setting)

        tach_needle_x = int(self.tachometer_gauge.gauge_center[0] - rotated_tachneedle.width() / 2)
        tach_needle_y = int(self.tachometer_gauge.gauge_center[1] - rotated_tachneedle.height() / 2)
        boost_needle_x = int(self.boost_gauge.gauge_center[0] - rotated_boostneedle.width() / 2)
        boost_needle_y = int(self.boost_gauge.gauge_center[1] - rotated_boostneedle.height() / 2)
        temp_needle_x = int(self.temp_gauge.gauge_center[0] - rotated_tempneedle.width() / 2)
        temp_needle_y = int(self.temp_gauge.gauge_center[1] - rotated_tempneedle.height() / 2)
        fuel_needle_x = int(self.fuel_gauge.gauge_center[0] - rotated_fuelneedle.width() / 2)
        fuel_needle_y = int(self.fuel_gauge.gauge_center[1] - rotated_fuelneedle.height() / 2)
        brakebias_x = int(self.brakebias_knob.gauge_center[0] - rotated_brakebias.width() / 2)
        brakebias_y = int(self.brakebias_knob.gauge_center[1] - rotated_brakebias.height() / 2)
        boostknob_x = int(self.boost_knob.gauge_center[0] - rotated_boostknob.width() / 2)
        boostknob_y = int(self.boost_knob.gauge_center[1] - rotated_boostknob.height() / 2)

        temp_painter = QPainter(combined_image)
        temp_painter.drawPixmap(tach_needle_x, tach_needle_y, rotated_tachneedle)
        temp_painter.drawPixmap(boost_needle_x, boost_needle_y, rotated_boostneedle)
        temp_painter.drawPixmap(temp_needle_x, temp_needle_y, rotated_tempneedle)
        temp_painter.drawPixmap(fuel_needle_x, fuel_needle_y, rotated_fuelneedle)
        temp_painter.drawPixmap(brakebias_x, brakebias_y, rotated_brakebias)
        temp_painter.drawPixmap(boostknob_x, boostknob_y, rotated_boostknob)

        if self.rpm > self.rpm_threshold:
            temp_painter.drawPixmap(self.rpm_x, self.rpm_y, self.rpmlight)

        digit_1 = self.mph // 100
        digit_2 = (self.mph % 100) // 10
        digit_3 = self.mph % 10

        if digit_1 == 0 and digit_2 != 0:
            temp_painter.drawPixmap(self.lcd_speed2_x, self.lcd_speed2_y, self.digit_images[digit_2])
            temp_painter.drawPixmap(self.lcd_speed3_x, self.lcd_speed3_y,  self.digit_images[digit_3])
        elif digit_1 == 0 and digit_2 == 0:
            temp_painter.drawPixmap(self.lcd_speed3_x, self.lcd_speed3_y, self.digit_images[digit_3])
        else:
            temp_painter.drawPixmap(self.lcd_speed1_x, self.lcd_speed1_y, self.digit_images[digit_1])
            temp_painter.drawPixmap(self.lcd_speed2_x, self.lcd_speed2_y, self.digit_images[digit_2])
            temp_painter.drawPixmap(self.lcd_speed3_x, self.lcd_speed3_y, self.digit_images[digit_3])

        temp_painter.drawPixmap(self.lcd_gear_x, self.lcd_gear_y, self.digit_images[self.gear])
        temp_painter.drawPixmap(self.fbar_x, self.fbar_y, self.rollbar_images[self.f_rollbar])
        temp_painter.drawPixmap(self.rbar_x, self.rbar_y, self.rollbar_images[self.r_rollbar])
        temp_painter.drawPixmap(self.shifter_x, self.shifter_y, self.gear_images[self.gear - 1])

        if self.fuel < self.critical_fuel:
            self.blink_duration = 0.25
        else:
            self.blink_duration = 0.5

        if self.fuel < self.low_fuel:
            current_time = time.time()
            if current_time - self.last_blink_time > self.blink_duration:
                self.last_blink_time = current_time
                self.fuel_blinker = not self.fuel_blinker
        else:
            self.fuel_blinker = False

        if self.fuel_blinker:
            temp_painter.drawPixmap(self.fuel_x, self.fuel_y, self.fuellight)

        if self.temp >= self.high_temp:
            current_time = time.time()
            if current_time - self.temp_last_blink_time > self.temp_blink_duration:
                self.temp_last_blink_time = current_time
                self.temp_blinker = not self.temp_blinker
        else:
            self.temp_blinker = False

        if self.temp_blinker:
            temp_painter.drawPixmap(self.temp_x, self.temp_y, self.fuellight)

        temp_painter.end()

        scaled_image = combined_image.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
        painter.drawPixmap(0, 0, scaled_image)


        # Get actual dimensions of the drawn image
        scaled_width = scaled_image.width()
        scaled_height = scaled_image.height()

        # Draw HUD text elements
        painter.setFont(QFont("Arial", 64, QFont.Bold))

        for text, x_ratio, y_ratio, color in self.hud_texts:
            x = int(scaled_width * x_ratio)  # Relative to the drawn image
            y = int(scaled_height * y_ratio)

            if color == 'green':
                painter.setPen(Qt.green)
            elif color == 'red':
                painter.setPen(Qt.red)


            painter.drawText(x, y, text)


        painter.end()
