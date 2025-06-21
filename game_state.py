import time

class GameState:
    """
    Represents the current state of the game, holding various metrics such as RPM,
    temperature, fuel, speed, and gear. The class also tracks and adjusts the boost
    level dynamically based on readings.

    Attributes:
        rpm (int): Current engine RPM.
        temp (float): Current engine temperature.
        fuel (float): Current fuel level.
        mph (int): Current speed in mph.
        gear (int): Current gear.
        cur_boost (float): Current boost level.
        f_rollbar (int): Front rollbar setting.
        r_rollbar (int): Rear rollbar setting.
        brake (int): Current brake pressure.
        boost_knob (int): Current boost knob setting.
        laptime (float): Current lap time in seconds.
        boost_drop_rate_per_second (float): Rate of decrease for boost level per second.
        boost_climb_rate_per_second (float): Rate of increase for boost level per second.
        last_update_time (float): Timestamp of the last state update.

    Methods:
        update(rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake, boost_knob, laptime):
            Updates the game state with new readings.
        update_boost(boost_reading):
            Interpolates and adjusts the current boost level based on the latest reading.
    """
    def __init__(self):
        self.rpm = 0
        self.temp = 0
        self.fuel = 0
        self.mph = 0
        self.gear = 1
        self.cur_boost = 30
        self.f_rollbar = 0
        self.r_rollbar = 0
        self.brake = 0
        self.last_update_time = time.time()
        self.boost_drop_rate_per_second = 0
        self.boost_climb_rate_per_second = 0
        self.boost_knob = 1
        self.laptime = 0

    def update(self, rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake, boost_knob, laptime):
        """
        Updates the game state with new readings from the dashboard.

        Args:
            rpm (int): Current engine RPM.
            boost (float): Current boost level.
            temp (float): Current engine temperature.
            fuel (float): Current fuel level.
            mph (int): Current speed in mph.
            gear (int): Current gear.
            f_rollbar (int): Front rollbar setting.
            r_rollbar (int): Rear rollbar setting.
            brake (int): Brake pressure.
            boost_knob (int): Boost knob setting.
            laptime (float): Current lap time in seconds.
        """
        self.rpm = rpm
        self.temp = temp
        self.fuel = fuel
        self.mph = mph
        self.gear = gear
        self.f_rollbar = f_rollbar
        self.r_rollbar = r_rollbar
        self.brake = brake
        self.update_boost(boost)
        self.boost_knob = boost_knob
        self.laptime = laptime

    def update_boost(self, boost_reading):
        """
        Interpolates and adjusts the current boost level based on the latest reading.

        The method calculates the fractional boost value by interpolating towards the
        current boost reading at a rate determined by `boost_drop_rate_per_second` or
        `boost_climb_rate_per_second`. If the difference between the interpolated value
        and the reading exceeds a threshold, the value is reset.

        Args:
            boost_reading (float): The boost value from the latest dashboard update.
        """
        current_time = time.time()
        time_delta = current_time - self.last_update_time

        # Interpolate boost value
        if boost_reading < self.cur_boost:
            self.cur_boost -= self.boost_drop_rate_per_second * time_delta
        elif boost_reading > self.cur_boost:
            self.cur_boost += self.boost_climb_rate_per_second * time_delta

        # Reset boost to the reading if the difference exceeds a threshold (e.g., 15)
        if abs(boost_reading - self.cur_boost) > 15:
            self.cur_boost = boost_reading

        self.last_update_time = current_time
