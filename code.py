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

led1 = RandomLED(board.GP5, 1.0)
led2 = RandomLED(board.GP6, 0.5)
ledY = RandomLED(board.GP7, 0.5)
ledR = RandomLED(board.GP8, 0.25)
ledG = RandomLED(board.GP9, 1.0)
board_pin = digitalio.DigitalInOut(board.GP10)
board_pin.direction = digitalio.Direction.OUTPUT

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
    print("Initializing Active Search Mode...")
    board_pin.value = False
    time.sleep(0.5)
    board_pin.value = True
    print("Active Search Mode Initialized.")

# Button release handlers
def btn1_released():
    global current_state
    if current_state == STATE_IDLE:
        current_state = STATE_ACTIVE_1
        play_wav(SOUND_FILES["active1"], loop=True)
    else:
        current_state = STATE_IDLE
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
print("Initializing Psychokinetic Energy Meter...")
board_pin.value = True
led1.off(); led2.off(); ledY.off(); ledR.off(); ledG.off()

play_wav(SOUND_FILES["start"])
time.sleep(1)
play_wav(SOUND_FILES["idle"], loop=True)
print("Boot Sequence Completed.")

# Main loop
while True:
    btn1.update()
    btn2.update()

    if btn1.fell:
        btn1_released()
    if btn2.fell:
        btn2_released()

    if current_state == STATE_IDLE:
        led1.blink = True
        led2.blink = True
        ledG.blink = True
        ledY.blink = True
        ledR.blink = False
        led1.update(); led2.update(); ledG.update(); ledY.update(); ledR.off()
    elif current_state == STATE_ACTIVE_1:
        led1.blink = False
        led2.blink = True
        ledG.blink = False
        ledY.blink = True
        ledR.blink = False
        led1.update(); led2.update(); ledG.update(); ledY.update(); ledR.off()
    elif current_state == STATE_ACTIVE_2:
        led1.blink = False
        led2.blink = False
        ledG.blink = False
        ledY.blink = False
        ledR.blink = True
        led1.update(); led2.update(); ledG.update(); ledY.update(); ledR.update()

    time.sleep(0.01)
