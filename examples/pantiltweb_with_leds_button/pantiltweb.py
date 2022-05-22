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

# Variables for the Debounce
uPressed = 0
upCompletePress = 0
upReleased = 0
downPressed = 0
downReleased = 0
downCompletePress = 0

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
GPIO.setup(ce0, GPIO.IN)
GPIO.setup(sclk, GPIO.OUT)
GPIO.setup(mosi, GPIO.IN)
GPIO.setup(miso, GPIO.OUT)

# Initialize the spi
try:
    spi = spidev.SpiDev()

    # Open a connection to a specific bus and device (chip select pin)
    #spi.open(bus, device) # moved to func spi_rx()

    # set SPI speed and mode
    # spi.max_speed_hz = 500000
    # spi.mode = 0
    # spi.dataLength = 3
except IOError as exc:
    print("Error opening /dev/spidev3.%d: %s" % (0, exc))
    raise

try:
    from flask import Flask, render_template
except ImportError:
    exit("This script requires the flask module\nInstall with: sudo pip install flask")

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('gui.html')

no_btn = 0
ctr_btn = 0x65 # = 101 dec -- Javascript keypress key-codes
rt_btn = 0x27  # =  39 dec
dn_btn = 0x28  # =  40 dec
lt_btn = 0x25  # =  37 dec
up_btn = 0x26  # =  38 dec
btn_val = no_btn
leds_state = 0

@app.route('/spi_rx/')
def spi_rx():
    n = 3
    rx_buf = bytes([0x0, 0x0, 0x0])
    if GPIO.input(ce0):
        # open spi port 0, device (ce0) 1
        spi.open(0,0)
        rx_buf = spi.readbytes(n) 
        spi.close()
        if isinstance(rx_buf, bytes):
            # position is the value from the rotary.encoder connected to Feather M4 Express
            position = rx_buf[1]
            if rx_buf[0] == 1: # the position value is negative    
                position *=-1 # make the value negative

            if position >= 0:
                direction = 1
            else:
                direction = 0
                
            button = rx_buf[2]
            if button > no_btn:
                if button == ctr_btn:
                    leds_setall((50,))  # Toggle the LED RGBW strip
                    return
                if button == up_btn:
                    direction = 'tilt';
                    angle = 1;
                elif button == dn_btn:
                    direction = 'tilt';
                    angle = -1;
                elif button == rt_btn:
                    direction = 'pan';
                    angle = -1;
                elif button == lt_btn:
                    direction = 'pan';
                    angle = 1;
                api(direction,  angle)

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

def buildReadCommand(channel):
    startBit = 0x01
    singleEnded = 0x08

    # Return python list of 3 bytes
    #   Build a python list using [1, 2, 3]
    #   First byte is the start bit
    #   Second byte contains single ended along with channel #
    #   3rd byte is 0
    return []
    
def processAdcValue(result):
    '''Take in result as array of three bytes. 
       Return the two lowest bits of the 2nd byte and
       all of the third byte'''
    pass
        
@app.route('/readAdc/')
def readAdc(channel):
    if ((channel > 7) or (channel < 0)):
        return -1
    r = spi.xfer2(buildReadCommand(channel))
    return processAdcValue(r)
   
"""
if len(argv)<2 or len(argv)>5:
    sys.stderr.write( "Syntax: {0} [<red> <green> <blue>] [<white>]\n".format(argv[0]) )
    exit(1)
"""

"""
   Function added by @Paulskpt to facilitate the 
   control of the 8 LED RGBW strip
   not initiated with external parameters as it was originally,
   but called from within this script
   If the middle button of the Adafruit rotary encoder is pressed,
   all leds will lit (in white).
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
        
    elif isinstance(rgbw, tuple):
        le = len(rgbw)
        red   = rgbw[0] if le > 2 else 0
        green = rgbw[1] if le > 2 else 0
        blue  = rgbw[2] if le > 2 else 0
        white = rgbw[3] if le > 3 else 0
        white = rgbw[0] if le == 1 else white

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
    try:
        while True:
            val = readAdc(0)
            print("ADC Result: ", str(val))
            time.sleep(5)
    except KeyboardInterrupt:
        spi.close() 
        sys.exit(0)

