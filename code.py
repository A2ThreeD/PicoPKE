# PicoPKE
# File: code.py
# Author: Aaron Morris / A2ThreeD
# Date: 2025-05-19
# Description: Code to play higher quality sound effects out of an I2S amplifier using a RP2040 board and interface to a Spirit PKE Meter prop.

import time
import board
import digitalio
import audiocore
import audiobusio
import os
from adafruit_debouncer import Debouncer

# Define sound files (must be WAV PCM 16-bit Mono 22KHz recommended)
SOUND_FILES = {
    "start": "sounds/startup.wav",
    "idle": "sounds/idle.wav",
    "active1": "sounds/active1.wav",
    "active2": "sounds/active2.wav",
}

# Audio setup (I2S)
audio = audiobusio.I2SOut(board.GP0, board.GP1, board.GP2)

# Button setup
def make_button(pin):
    pin_in = digitalio.DigitalInOut(pin)
    pin_in.direction = digitalio.Direction.INPUT
    pin_in.pull = digitalio.Pull.UP
    return Debouncer(pin_in)

btn1 = make_button(board.GP3)
btn2 = make_button(board.GP4)

# LED setup
class RandomLED:
    def __init__(self, pin, interval, blink=True):
        self.pin = digitalio.DigitalInOut(pin)
        self.pin.direction = digitalio.Direction.OUTPUT
        self.interval = interval
        self.blink = blink
        self.last_time = time.monotonic()
        self.state = False

    def update(self):
        if not self.blink:
            self.pin.value = True
            return
        now = time.monotonic()
        if now - self.last_time >= self.interval:
            self.state = not self.state
            self.pin.value = self.state
            self.last_time = now

    def off(self):
        self.pin.value = False

# LED output pins
led1 = RandomLED(board.GP5, 1.0)
led2 = RandomLED(board.GP6, 0.5)
ledYellow = RandomLED(board.GP7, 0.5)
ledRed = RandomLED(board.GP8, 0.25)
ledGreen = RandomLED(board.GP9, 1.0)

# Define pin for outputting to Spirit PKE PCB
board_pin = digitalio.DigitalInOut(board.GP10)
board_pin.direction = digitalio.Direction.OUTPUT

# Button Defaults
btn1_held_time = None

# State constants
STATE_IDLE = 0
STATE_ACTIVE_1 = 1
STATE_ACTIVE_2 = 2
current_state = STATE_IDLE

# Helper: Play WAV file
def play_wav(filename, loop=False):
    try:
        wave_file = open(filename, "rb")
        wave = audiocore.WaveFile(wave_file)
        if loop:
            audio.play(wave, loop=True)
        else:
            audio.play(wave)
            while audio.playing:
                time.sleep(0.1)
    except Exception as e:
        print("Audio error:", e)

# Simulate button press action
def simulate_button_press():
    print ("Sending button press to Spirit PKE ... ")
    board_pin.value = False
    time.sleep(0.5)
    board_pin.value = True

# Button release handlers
def btn1_released():
    global current_state
    if current_state == STATE_IDLE:
        current_state = STATE_ACTIVE_1
        print("Entering Active State 1 ...")
        play_wav(SOUND_FILES["active1"], loop=True)
    else:
        current_state = STATE_IDLE
        print("Entering Idle State ...")
        play_wav(SOUND_FILES["idle"], loop=True)
    simulate_button_press()

def btn2_released():
    global current_state
    if current_state == STATE_IDLE:
        return
    if current_state == STATE_ACTIVE_1:
        current_state = STATE_ACTIVE_2
        play_wav(SOUND_FILES["active2"], loop=True)
    elif current_state == STATE_ACTIVE_2:
        current_state = STATE_ACTIVE_1
        play_wav(SOUND_FILES["active1"], loop=True)

# Initial boot sequence
print("Starting Up PicoPKE ... ")
board_pin.value = True
led1.off(); led2.off(); ledYellow.off(); ledRed.off(); ledGreen.off()

#Play bootup sound and then start with the idling sounds
play_wav(SOUND_FILES["start"])
time.sleep(1)
play_wav(SOUND_FILES["idle"], loop=True)

print("PKE Meter Booted and Idling")

# Main loop
while True:
    btn1.update()
    btn2.update()

    if btn1.fell:
        btn1_held_time = time.monotonic()
    if btn2.fell:
        btn2_released()

    #If the left button is held down, mute the audio and go into idle.
    if btn1.value == False and btn1_held_time is not None:
        held_duration = time.monotonic() - btn1_held_time
        if held_duration > 1.0:
            print("Button 1 held > 1 second. Stopping audio.")
            audio.stop()
            current_state = STATE_IDLE
            btn1_held_time = None
            # Optionally turn off all LEDs
            for led in [led1, led2, ledGreen, ledYellow, ledRed]:
                led.off()

    elif btn1.rose and btn1_held_time is not None:
        # Only trigger released if held less than 1 sec
        held_duration = time.monotonic() - btn1_held_time
        if held_duration <= 1.0:
            btn1_released()
        btn1_held_time = None

    #Based on the state buttons, blink different LEDs
    if current_state == STATE_IDLE:
        led1.blink = True
        led2.blink = True
        ledGreen.blink = True
        ledYellow.blink = True
        ledRed.blink = False
        led1.update(); led2.update(); ledGreen.update(); ledYellow.update(); ledRed.off()
    elif current_state == STATE_ACTIVE_1:
        led1.blink = False
        led2.blink = True
        ledGreen.blink = False
        ledYellow.blink = True
        ledRed.blink = False
        led1.update(); led2.update(); ledGreen.update(); ledYellow.update(); ledRed.off()
    elif current_state == STATE_ACTIVE_2:
        led1.blink = False
        led2.blink = False
        ledGreen.blink = False
        ledYellow.blink = False
        ledRed.blink = True
        led1.update(); led2.update(); ledGreen.update(); ledYellow.update(); ledRed.update()

    time.sleep(0.01)
