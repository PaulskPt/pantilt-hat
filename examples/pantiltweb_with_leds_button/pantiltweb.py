#!/usr/bin/env python
import pantilthat
from sys import exit
import RPi.GPIO  as GPIO
import spidev
import time

# we only have SPI 0 bus to us on the Pi
bus = 0

#Device is the chip select pin. Set to 0 or 1, depending on the connections
device = 0
ce0 = 8
mosi = 10
miso = 9
sclk = 11

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
GPIO.setup(ce0, GPIO.IN)
GPIO.setup(sclk, GPIO.OUT)
GPIO.setup(mosi, GPIO.IN)
GPIO.setup(miso, GPIO.OUT)

leds_state = 0

# Initialize the spi
try:
    spi = spidev.SpiDev()
except IOError as exc:
    print("Error opening /dev/spidev0.%d: %s" % (0, exc))
    raise

try:
    from flask import Flask, render_template
except ImportError:
    exit("This script requires the flask module\nInstall with: sudo pip install flask")

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('gui.html')


@app.route('/api/<direction>/<int:angle>')
def api(direction, angle):
    if angle < 0 or angle > 180:
        return "{'error':'out of range'}"

    angle -= 90

    if direction == 'pan':
        pantilthat.pan(angle)
        return "{{'pan':{}}}".format(angle)

    elif direction == 'tilt':
        pantilthat.tilt(angle)
        return "{{'tilt':{}}}".format(angle)


"""
   Function added by @Paulskpt to facilitate the 
   control of the 8 LED RGBW strip
   If the middle button of the Adafruit ANO rotary encoder is pressed,
   or the 'Leds' (middle) button on the webinterface is pressed,
   all leds will switch ON (white color) or off (toggle function).
"""
@app.route('/leds_setall/<int:rgbw>')
def leds_setall(rgbw):
    global leds_state
    pantilthat.light_mode(pantilthat.WS2812)
    pantilthat.light_type(pantilthat.GRBW)
    
    if rgbw is None:
        if leds_state == 0:
            red = 0
            green = 0
            blue = 0
            white = 255
    elif isinstance(rgbw, int):
        if leds_state == 0:
            red = 0
            green = 0
            blue = 0
            white = rgbw


    if leds_state == 0:
        leds_state = 1 # flip
        pantilthat.set_all(red, green, blue, white)
    elif leds_state == 1:
        leds_state = 0 # flip
        pantilthat.clear()
    pantilthat.show()
    return '200'  # The gui.html with Flake expect a string, dict, tuple response instance
                
                
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9595, debug=True)
 

