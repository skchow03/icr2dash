import keyboard
import pygame
import time
import threading
from enum import Enum
from utils import play_gear_grinding_sound, stop_gear_grinding_sound

class GearHandler:
    def __init__(self, game_state, config, overlay_handler):
        self.gs = game_state
        self.overlay_handler = overlay_handler
        self.config = config

        self.gear_lock = threading.Lock()
        self.target_gear = 1
        self.clutch_engaged = False
        self.gears_grind = False
        self.last_gear_change = 1

        # Initialize pygame mixer
        pygame.mixer.init()
        self.gear_grinding_sound = pygame.mixer.Sound("assets/sounds/shfterr.wav")
        self.gear_grinding_sound.set_volume(config.getfloat('Gear shifting', 'gear_grinding_volume'))
        self.gear_grinding_channel = pygame.mixer.Channel(0)

        self.shifter_gear1_key = config.get('Gear shifting', 'shifter_gear1_key')
        self.shifter_gear2_key = config.get('Gear shifting', 'shifter_gear2_key')
        self.shifter_gear3_key = config.get('Gear shifting', 'shifter_gear3_key')
        self.shifter_gear4_key = config.get('Gear shifting', 'shifter_gear4_key')
        self.shifter_gear5_key = config.get('Gear shifting', 'shifter_gear5_key')
        self.shifter_gear6_key = config.get('Gear shifting', 'shifter_gear6_key')

        self.hshifter_on = config.get('Gear shifting', 'hshifter').lower() == 'on'
        self.clutch_on = config.get('Gear shifting', 'clutch').lower() == 'on'

        self.clutch_key = config.get('Gear shifting', 'clutch_key')
        self.upshift_delay = config.getfloat('Gear shifting', 'upshift_delay')
        self.downshift_delay = config.getfloat('Gear shifting', 'downshift_delay')
        self.key_listener_delay = config.getfloat('General', 'key_listener_delay')
        self.icr2_shiftup_key = config.get('Gear shifting','icr2_shiftup_key')
        self.icr2_shiftdown_key = config.get('Gear shifting','icr2_shiftdown_key')

        print("GearHandler initialized with the following settings:")
        print (f"  shifter_gear1_key: {self.shifter_gear1_key}")
        print (f"  shifter_gear2_key: {self.shifter_gear2_key}")
        print (f"  shifter_gear3_key: {self.shifter_gear3_key}")
        print (f"  shifter_gear4_key: {self.shifter_gear4_key}")
        print (f"  shifter_gear5_key: {self.shifter_gear5_key}")
        print (f"  shifter_gear6_key: {self.shifter_gear6_key}")
        print(f"  clutch_key: {self.clutch_key}")
        print (f"  icr2_shiftup_key: {self.icr2_shiftup_key}")
        print (f"  icr2_shiftdown_key: {self.icr2_shiftdown_key}")
        print(f"  upshift_delay: {self.upshift_delay}")
        print(f"  downshift_delay: {self.downshift_delay}")
        print(f"  key_listener_delay: {self.key_listener_delay}")
        print(f"  H-shifter on: {self.hshifter_on}")
        print(f"  Clutch on: {self.clutch_on}")

    def send_keypress(self, key):
        """Send a keypress to the system."""
        keyboard.send(key)

    def detect_pressed_gear(self):
        """Detect which shifter gear key is currently pressed."""
        if keyboard.is_pressed(self.shifter_gear1_key):
            return 1
        if keyboard.is_pressed(self.shifter_gear2_key):
            return 2
        if keyboard.is_pressed(self.shifter_gear3_key):
            return 3
        if keyboard.is_pressed(self.shifter_gear4_key):
            return 4
        if keyboard.is_pressed(self.shifter_gear5_key):
            return 5
        if keyboard.is_pressed(self.shifter_gear6_key):
            return 6
        return 0

    def gear_change_listener(self, gs, stop_event):

        self.lock_shift = False

        if self.clutch_on:
            while not stop_event.is_set():

                # Detect if shifter gear key is pressed
                self.pressed_gear = self.detect_pressed_gear()

                # Detect if clutch is pressed
                if keyboard.is_pressed(self.clutch_key):
                    self.clutch_engaged = True
                else:
                    self.clutch_engaged = False

                #print (f'Gear: {self.pressed_gear} Clutch: {self.clutch_engaged} Gear grinding: {self.gears_grind} Target gear: {self.target_gear}')            

                # If the shifter is put into neutral for any reason, release the
                # lock on shifting.
                if self.target_gear == 0:
                    self.lock_shift = False

                # If the shifter is put into neutral, then set the target gear to
                # zero (or neutral). If gears were grinding, then stop gears grinding.
                if self.pressed_gear == 0:
                    self.target_gear = 0
                    self.gears_grind = False
                    stop_gear_grinding_sound(self.gear_grinding_channel)

                # If the shifter is in gear, and shifter was previously in neutral
                # (i.e. target gear is zero), and the clutch is not pressed, then
                # start the gears grinding.
                if self.pressed_gear > 0 and not self.clutch_engaged and self.target_gear == 0:
                    self.gears_grind = True
                    play_gear_grinding_sound(self.gear_grinding_channel, self.gear_grinding_sound)

                # If the shifter is in gear, and clutch is engaged, and the gears
                # are not already grinding from a previous inappropriate shift,
                # then set the target gear to the selected shifter gear. Note this
                # does not send the key to the game to shift yet - that only happens
                # when the clutch is released.
                if self.pressed_gear > 0 and self.clutch_engaged and not self.gears_grind:
                    self.target_gear = self.pressed_gear

                if not self.clutch_engaged and self.target_gear > 0 and not self.lock_shift:
                    #print (f'Gear: {self.pressed_gear} | Clutch: {self.clutch_engaged} | Gear grinding: {self.gears_grind} | Target gear: {self.target_gear} | Game gear: {gs.gear}')
                    
                    if self.target_gear > gs.gear:
                        num_shifts = self.target_gear - gs.gear
                        self.lock_shift = True
                        #print (f'Sending {num_shifts} upshift(s) from {gs.gear} to {self.target_gear}')
                        for _ in range(0, num_shifts):
                            self.send_keypress(self.icr2_shiftup_key)
                            time.sleep(self.upshift_delay)
                    elif self.target_gear < gs.gear:
                        num_shifts = gs.gear - self.target_gear
                        self.lock_shift = True
                        #print (f'Sending {num_shifts} downshift(s) from {gs.gear} to {self.target_gear}')
                        for _ in range(0, num_shifts):
                            self.send_keypress(self.icr2_shiftdown_key)
                            time.sleep(self.downshift_delay)
                    else:
                        self.lock_shift = True
                        #print ('Same gear - no shift')
                
                time.sleep(self.key_listener_delay)
        else:
            while not stop_event.is_set():

                # Detect if shifter gear key is pressed
                self.pressed_gear = self.detect_pressed_gear()
                if self.pressed_gear > 0:
                    self.target_gear = self.pressed_gear

                if self.target_gear == gs.gear:
                    self.lock_shift = False

                if not self.lock_shift:
                    if self.target_gear > gs.gear:
                        num_shifts = self.target_gear - gs.gear
                        self.lock_shift = True
                        for _ in range(0, num_shifts):
                            self.send_keypress(self.icr2_shiftup_key)
                            time.sleep(self.upshift_delay)
                    elif self.target_gear < gs.gear:
                        num_shifts = gs.gear - self.target_gear
                        self.lock_shift = True
                        for _ in range(0, num_shifts):
                            self.send_keypress(self.icr2_shiftdown_key)
                            time.sleep(self.downshift_delay)
                
                time.sleep(self.key_listener_delay)