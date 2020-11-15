from gpiozero import LED
from time import sleep
import RPi.GPIO as GPIO

channel = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(channel, GPIO.IN)


def callback(channel):
    print(GPIO.input(channel))
    if GPIO.input(channel):
        print("no water detected")
    else:
        print("water detected")

#GPIO.add_event_detect(channel, GPIO.BOTH, bouncetime=300)
#GPIO.add_event_callback(channel, callback)

led = LED(14)


while True:
    sleep(1)
    if GPIO.input(channel):
        led.off()
    else:
        led.on()

