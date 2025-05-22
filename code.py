# PicoPKE
# File: code.py
# Author: Aaron Morris / A2ThreeD
# Date: 2025-05-21
# Version: 1.0
# Description: CircuitPython code to play higher quality sound effects out of an I2S amplifier using a RP2040 board and interface to a Spirit PKE Meter prop.

import time
import board
import digitalio
import audiocore
import audiobusio
import asyncio
import os
from adafruit_debouncer import Button

# Define sound files (must be WAV PCM 16-bit Mono 22KHz recommended)
SOUND_FILES = {
    "start": "sounds/pkestartup.wav",
    "low": "sounds/pkelow.wav",
    "medium": "sounds/pkemedium.wav",
    "high": "sounds/pkehigh.wav",
}

# Audio setup (I2S)
audio = audiobusio.I2SOut(board.GP0, board.GP1, board.GP2)

# Button setup
button1_pin = digitalio.DigitalInOut(board.GP3)
button1_pin.direction = digitalio.Direction.INPUT
button1_pin.pull = digitalio.Pull.UP
button1 = Button(button1_pin)

# Limit switch setup
llswitch_pin = digitalio.DigitalInOut(board.GP5)
llswitch_pin.direction = digitalio.Direction.INPUT
llswitch_pin.pull = digitalio.Pull.UP
llswitch = Button(llswitch_pin)

# Define pin for outputting button1 pulse to Spirit PKE PCB
board_pin = digitalio.DigitalInOut(board.GP10)
board_pin.direction = digitalio.Direction.OUTPUT
board_pin.value = False

# Define pin for outputting limit pulse to Spirit PKE PCB
lowerlimit_pin = digitalio.DigitalInOut(board.GP11)
lowerlimit_pin.direction = digitalio.Direction.OUTPUT
lowerlimit_pin.value = False

# Define state variables to track the different modes/sounds
STATE_BOOTING = 0
STATE_BOOTED = 1
STATE_LOW = 2
STATE_MEDIUM = 3
STATE_HIGH = 4
STATE_MUTE = 5

#Default state should be set to STATE_BOOTING
current_state = STATE_BOOTING

async def play_wav(filename, loop=False):
    try:
        wave_file = open(filename, "rb")
        wave = audiocore.WaveFile(wave_file)
        if loop:
            audio.play(wave, loop=True)
        else:
            audio.play(wave)
            while audio.playing:
                await asyncio.sleep(0.05)
    except Exception as e:
        print("Audio error:", e)

def send_button_press():
    print ("Sending button press to Spirit PKE ... ")

    #Create a 250ms pulse to tell the Spirit PKE PCB that the left button was pressed
    board_pin.value = True
    time.sleep(0.25)
    board_pin.value = False

async def short_press():
    global current_state
    print("Short press detected!")

    #If this is a button press when the wings are down, change the state and play the medium speed scanning sound.
    if current_state == STATE_BOOTED:
        await play_wav(SOUND_FILES["medium"], loop=True)
        current_state = STATE_MEDIUM

    #Send the button pulse to the Spirit PKE PCB
    send_button_press()

async def long_press():
    print("Long press detected!")

    global current_state
    if current_state == STATE_LOW:
        current_state = STATE_MEDIUM
        print("Medium Speed ...")
        await play_wav(SOUND_FILES["medium"], loop=True)
    elif current_state == STATE_MEDIUM:
        current_state = STATE_HIGH
        print("High Speed...")
        await play_wav(SOUND_FILES["high"], loop=True)
    elif current_state == STATE_HIGH:
        current_state = STATE_LOW
        print("Low Speed...")
        await play_wav(SOUND_FILES["low"], loop=True)

async def main_loop():
    global current_state
    print("Starting Up PicoPKE ... ")
    await play_wav(SOUND_FILES["start"])
    print("PKE Meter Booted")
    current_state = STATE_BOOTED

    while True:

        #Get the status of the buttons and limit switches
        button1.update()
        llswitch.update()

        #If the left button is pressed, determine if it's long or short and change the sounds appropriately.
        if button1.long_press:
            await long_press()
        if button1.short_count !=0:
            await short_press()

        if llswitch.value:
            #print('Lower motor limit not triggered - Wings up')
            lowerlimit_pin.value = False
        else:
            lowerlimit_pin.value = True

            #Only stop the audio and reset the state if the lower limit switch was just pressed
            if llswitch.fell:
                print('Lower motor limit triggered - Wings are down')
                audio.stop()
                current_state = STATE_BOOTED


        await asyncio.sleep(0.01)  # small yield

asyncio.run(main_loop())
