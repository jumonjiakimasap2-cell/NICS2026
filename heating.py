import RPi.GPIO as GPIO
import time

heating_wire = 17

print("start")

GPIO.setmode(GPIO.BCM)
GPIO.setup(heating_wire, GPIO.OUT)

try:
    print("fire")
    GPIO.output(heating_wire, GPIO.HIGH)

    time.sleep(3)

    GPIO.output(heating_wire, GPIO.LOW)
    print("done")

except KeyboardInterrupt:
    print("stopped")

finally:
    GPIO.cleanup()
