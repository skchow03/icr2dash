import time
import datetime

class telemetry:
    def __init__(self):
        self.laptimes_list = []
        self.lap_dist = 0
        self.last_split = 0
        self.lap_counter = 0
        self.start_real_time = time.time()
        self.last_lcd_time = 0
        self.last_lcd_refresh = time.time()
        self.time_added = False
        self.fuel_list = []

        now = datetime.datetime.now()
        # Format the date and time
        formatted_date = now.strftime("%Y-%m-%d")  # Example: 2025-01-21
        formatted_time = now.strftime("%H-%M-%S")  # Example: 14-30-45

        # Create the filename
        self.filename = f"telemetry_{formatted_date}_{formatted_time}.csv"

        print (f'Initialized telemetry as {self.filename}')
        with open(self.filename, "w") as o:
            o.write('lap,laptime,fuel\n')


    def export_telemetry(self, lapnum, laptime, fuel):
        with open(self.filename, "a") as o:
            o.write(f'{lapnum},{laptime},{fuel}\n')

    def reset(self):
        #self.export_telemetry()
        self.laptimes_list = []
        self.fuel_list = []
        self.lap_counter = 0
        print ('Telemetry reset (lap counter back to zero)')
    
    def update(self, lcd_time, fuel):
        real_time = time.time()
        if lcd_time > self.last_lcd_time:
            # LCD has advanced since the last LCD time
            self.last_lcd_time = lcd_time
            self.last_lcd_refresh = real_time
            self.time_added = False
        elif lcd_time < self.last_lcd_time:
            # LCD has gone backwards, which only happens when Shift-R or new lap
            if not self.time_added:
                self.laptimes_list.append(self.last_lcd_time)
                self.fuel_list.append(fuel)
                #print(f'Lap {self.lap_counter}, time {self.last_lcd_time}, fuel {fuel}')
                #self.export_telemetry(self.lap_counter, self.last_lcd_time, fuel)

                self.lap_counter += 1
            self.last_lcd_time = lcd_time
            self.last_lcd_refresh = real_time
            self.time_added = True
        elif lcd_time == self.last_lcd_time:
            # LCD time is the same as previous LCD time
            time_since_refresh = real_time - self.last_lcd_refresh
            if time_since_refresh > 0.1 and not self.time_added:
                self.laptimes_list.append(lcd_time)
                self.fuel_list.append(fuel)
                self.time_added = True    # Add flag to prevent more time added until next refresh
                #print(f'Lap {self.lap_counter}, time {self.last_lcd_time}, fuel {fuel}')
                #self.export_telemetry(self.lap_counter, self.last_lcd_time, fuel)

                self.lap_counter += 1