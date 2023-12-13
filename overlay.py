from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPixmap, QTransform
from PyQt5.QtCore import Qt
from PIL import Image
import time

class Gauge:
    def __init__(self, needle_image_path, pivot, min_value, max_value, gauge_center,
                 section_one_end, section_two_start, min_angle, max_angle_section_one, max_angle_section_two):
        self.needle_image = QPixmap(needle_image_path)
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
        if value <= self.section_one_end:
            # If in the first section, map the value to the first angle range
            angle_range = self.max_angle_section_one - self.min_angle
            value_range = self.section_one_end - self.min_value
            angle = ((value - self.min_value) / value_range) * angle_range + self.min_angle
        else:
            # If in the second section, map the value to the second angle range
            angle_range = self.max_angle_section_two - self.max_angle_section_one
            value_range = self.max_value - self.section_two_start
            angle = ((value - self.section_two_start) / value_range) * angle_range + self.max_angle_section_one

        # Rotate the needle image around the pivot
        transform = QTransform().translate(self.pivot[0], self.pivot[1]).rotate(-angle).translate(-self.pivot[0], -self.pivot[1])
        return self.needle_image.transformed(transform)





class CockpitOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Load the cockpit image
        self.image = QPixmap("assets/cockpit/lola87.png")

        # Initialize the tachometer gauge with non-linear sections
        self.tachometer_gauge = Gauge(
            needle_image_path="assets/cockpit/tachneedle.png",
            pivot=(45, 45),  # Pivot point of the needle image
            min_value=0,
            max_value=1500,
            gauge_center=(415, 362),
            section_one_end=600,  # End of the first section
            section_two_start=600,  # Start of the second section (can be the same as section_one_end if continuous)
            min_angle=222,  # Starting angle for the first section
            max_angle_section_one=180,  # Ending angle for the first section
            max_angle_section_two=-47  # Ending angle for the second section
        )

        self.boost_gauge = Gauge(
            needle_image_path="assets/cockpit/tachneedle.png",
            pivot=(45, 45),  # Pivot point of the needle image
            min_value=30,
            max_value=45,
            gauge_center=(234, 360),
            section_one_end=31,  # End of the first section
            section_two_start=31,  # Start of the second section (can be the same as section_one_end if continuous)
            min_angle=80,  # Starting angle for the first section
            max_angle_section_one=75,  # Ending angle for the first section
            max_angle_section_two=0  # Ending angle for the second section
        )

        self.temp_gauge = Gauge(
            needle_image_path="assets/cockpit/tempneedle.png",
            pivot=(29, 29),  # Pivot point of the needle image
            min_value=180,
            max_value=250,
            gauge_center=(322, 341),
            section_one_end=181,  # End of the first section
            section_two_start=181,  # Start of the second section (can be the same as section_one_end if continuous)
            min_angle=56,  # Starting angle for the first section
            max_angle_section_one=55.5,  # Ending angle for the first section
            max_angle_section_two=-98  # Ending angle for the second section
        )

        self.fuel_gauge = Gauge(
            needle_image_path="assets/cockpit/fuelneedle.png",
            pivot=(25, 25),  # Pivot point of the needle image
            min_value=0,
            max_value=40,
            gauge_center=(325, 418),
            section_one_end=1,  # End of the first section
            section_two_start=1,  # Start of the second section (can be the same as section_one_end if continuous)
            min_angle=125,  # Starting angle for the first section
            max_angle_section_one=125-6.25,  # Ending angle for the first section
            max_angle_section_two=-125  # Ending angle for the second section
        )

        self.brakebias_knob = Gauge(
            needle_image_path="assets/cockpit/brakebias.png",
            pivot=(19, 19),
            min_value=0,
            max_value=7,
            gauge_center=(230,438),
            section_one_end=1,  # End of the first section
            section_two_start=1,  # Start of the second section (can be the same as section_one_end if continuous)
            min_angle=90,  # Starting angle for the first section
            max_angle_section_one=68,  # Ending angle for the first section
            max_angle_section_two=-90  # Ending angle for the second section
        )

        self.rpm = 0
        self.boost = 0
        self.temp = 0
        self.fuel = 0
        self.mph = 0
        self.rpm_threshold = 1300
        self.fuel_blinker = False
        self.blink_timer = 0
        self.blink_duration = 0.5
        self.last_blink_time = 0

        self.temp_blinker = False
        self.temp_blink_timer = 0
        self.temp_blink_duration = 0.5
        self.temp_last_blink_time = 0

        # Load LCD digits
        # Load the PNG image using QPixmap
        image_pixmap = QPixmap("assets/cockpit/lcdnums.png")

        # Assuming you have 10 digits (0 to 9), determine the coordinates and dimensions for each digit.
        # For example, if all digits are in a single row and have the same size, you can do the following:

        digit_width = image_pixmap.width() // 10  # Calculate the width of each digit
        digit_height = image_pixmap.height()  # Assume all digits have the same height

        self.digit_images = []  # List to store separate digit QPixmap objects

        for i in range(10):
            x = i * digit_width  # Calculate the x-coordinate of the digit
            y = 0  # Set the y-coordinate to 0 if all digits are in a single row

            # Crop the image to extract the digit
            digit_pixmap = image_pixmap.copy(x, y, digit_width, digit_height)

            # Append the QPixmap to the list
            self.digit_images.append(digit_pixmap)

        self.rollbar_images = [
            QPixmap("assets/cockpit/rollbar1.png"),
            QPixmap("assets/cockpit/rollbar2.png"),
            QPixmap("assets/cockpit/rollbar3.png"),
            QPixmap("assets/cockpit/rollbar4.png"),
            QPixmap("assets/cockpit/rollbar5.png"),
            QPixmap("assets/cockpit/rollbar6.png"),
            QPixmap("assets/cockpit/rollbar7.png"),
            QPixmap("assets/cockpit/rollbar8.png"),
        ]

        self.gear_images = [
            QPixmap("assets/cockpit/gear1.png"),
            QPixmap("assets/cockpit/gear2.png"),
            QPixmap("assets/cockpit/gear3.png"),
            QPixmap("assets/cockpit/gear4.png"),
            QPixmap("assets/cockpit/gear5.png"),
            QPixmap("assets/cockpit/gear6.png"),
        ]


    def setPositionAndSize(self, x, y, width, height):
        """Set the position and size of the overlay."""
        self.setGeometry(x, y, width, height)

    def setGauges(self, rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake):
        self.rpm = rpm
        self.boost = boost
        self.temp = temp
        self.fuel = fuel
        self.mph = mph
        self.gear = gear
        self.f_rollbar = f_rollbar
        self.r_rollbar = r_rollbar
        self.brake = brake
        self.update()  # Trigger a repaint


    def paintEvent(self, event):
        """Paint the cockpit overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create a temporary image to paint onto
        combined_image = self.image.copy()

        # RPM light
        rpmlight = QPixmap("assets/cockpit/redlit.png")
        # Fuel light
        fuellight = QPixmap("assets/cockpit/yellowlit.png")


        # Rotate the tachometer needle based on the current RPM
        rotated_tachneedle = self.tachometer_gauge.rotate_needle(self.rpm)
        rotated_boostneedle = self.boost_gauge.rotate_needle(self.boost)
        rotated_tempneedle = self.temp_gauge.rotate_needle(self.temp)
        rotated_fuelneedle = self.fuel_gauge.rotate_needle(self.fuel)
        rotated_brakebias = self.brakebias_knob.rotate_needle(self.brake)

        # Calculate the top-left position to ensure the needle is centered at the gauge center
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

        # Draw the rotated needle on the combined image
        temp_painter = QPainter(combined_image)
        temp_painter.drawPixmap(tach_needle_x, tach_needle_y, rotated_tachneedle)
        temp_painter.drawPixmap(boost_needle_x, boost_needle_y, rotated_boostneedle)
        temp_painter.drawPixmap(temp_needle_x, temp_needle_y, rotated_tempneedle)
        temp_painter.drawPixmap(fuel_needle_x, fuel_needle_y, rotated_fuelneedle)
        temp_painter.drawPixmap(brakebias_x, brakebias_y, rotated_brakebias)

        # Light up the RPM light if past RPM threshold
        if self.rpm > self.rpm_threshold:
            temp_painter.drawPixmap(363, 295, rpmlight)

        # LCD MPH display
        digit_1 = self.mph // 100  # Hundreds digit
        digit_2 = (self.mph % 100) // 10  # Tens digit
        digit_3 = self.mph % 10  # Ones digit

        if digit_1 == 0 and digit_2 != 0:
            temp_painter.drawPixmap(330, 282, self.digit_images[digit_2])
            temp_painter.drawPixmap(337, 282, self.digit_images[digit_3])
        elif digit_1 == 0 and digit_2 == 0:
            temp_painter.drawPixmap(337, 282, self.digit_images[digit_3])
        else:
            temp_painter.drawPixmap(323, 282, self.digit_images[digit_1])
            temp_painter.drawPixmap(330, 282, self.digit_images[digit_2])
            temp_painter.drawPixmap(337, 282, self.digit_images[digit_3])

        # Gear display
        temp_painter.drawPixmap(300, 282, self.digit_images[self.gear])

        # Rollbar display
        temp_painter.drawPixmap(-10, 404, self.rollbar_images[self.f_rollbar])    
        temp_painter.drawPixmap(20, 430, self.rollbar_images[self.r_rollbar])    
        temp_painter.drawPixmap(510, 411, self.gear_images[self.gear - 1])    

        # Fuel light
        if self.fuel < 1: 
            self.blink_duration = 0.25
        else:
            self.blink_duration = 0.5

        if self.fuel < 5:
            # Check if it's been long enough to toggle blinking
            current_time = time.time()
            if current_time - self.last_blink_time > self.blink_duration:
                self.last_blink_time = current_time   # Reset clock
                if self.fuel_blinker == True:
                    self.fuel_blinker = False
                elif self.fuel_blinker == False:
                    self.fuel_blinker = True
        else:
            self.fuel_blinker = False

        if self.fuel_blinker:
            temp_painter.drawPixmap(256, 415, fuellight) 

        # Temperature light
        if self.temp >= 220:
            # Check if it's been long enough to toggle blinking
            current_time = time.time()
            if current_time - self.temp_last_blink_time > self.temp_blink_duration:
                self.temp_last_blink_time = current_time   # Reset clock
                if self.temp_blinker == True:
                    self.temp_blinker = False
                elif self.temp_blinker == False:
                    self.temp_blinker = True
        else:
            self.temp_blinker = False

        if self.temp_blinker:
            temp_painter.drawPixmap(365, 415, fuellight) 



        temp_painter.end()

        # Now scale the combined image for display
        scaled_image = combined_image.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
        painter.drawPixmap(0, 0, scaled_image)

        painter.end()  # Finish the painting