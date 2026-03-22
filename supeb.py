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
    print("右バック・左前進（5秒）")

    # ===== 右モーター：バック =====
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)

    # ===== 左モーター：前進 =====
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)

    time.sleep(5)

    print("停止")

    # ===== 停止 =====
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.LOW)

except KeyboardInterrupt:
    print("Stop")

finally:
    pwmA.stop()
    pwmB.stop()
    GPIO.cleanup()
