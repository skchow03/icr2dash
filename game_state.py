import time

class GameState:
    """Holds and updates the game's current state."""
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

    def update(self, rpm, boost, temp, fuel, mph, gear, f_rollbar, r_rollbar, brake, boost_knob):
        """Update the game state based on new readings."""
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

    def update_boost(self, boost_reading):
        """Adjusts the boost value based on the current reading."""
        current_time = time.time()
        time_delta = current_time - self.last_update_time

        if boost_reading < self.cur_boost:
            self.cur_boost -= self.boost_drop_rate_per_second * time_delta
        elif boost_reading > self.cur_boost:
            self.cur_boost += self.boost_climb_rate_per_second * time_delta

        # Reset boost if deviation is significant
        if abs(boost_reading - self.cur_boost) > 15:
            self.cur_boost = boost_reading

        self.last_update_time = current_time
