import RPi.GPIO as GPIO
import time

# pin設定
PWMA = 18
AIN1 = 8
AIN2 = 25
PWMB = 10
BIN1 = 9
BIN2 = 11

frequency = 50

GPIO.setmode(GPIO.BCM)

GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(PWMB, GPIO.OUT)
GPIO.setup(BIN1, GPIO.OUT)
GPIO.setup(BIN2, GPIO.OUT)

# PWM設定
pwmA = GPIO.PWM(PWMA, frequency)
pwmB = GPIO.PWM(PWMB, frequency)

pwmA.start(100)
pwmB.start(100)

try:
    print("Forward")

    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Stop")

    pwmA.stop()
    pwmB.stop()

    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.LOW)

    GPIO.cleanup()
