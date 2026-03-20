import RPi.GPIO as GPIO
import time

def motor_thread(get_direction):

    # ===== ピン設定 =====
    PWMA = 18
    AIN1 = 8
    AIN2 = 25
    PWMB = 10
    BIN1 = 9
    BIN2 = 11

    GPIO.setup(PWMA, GPIO.OUT)
    GPIO.setup(AIN1, GPIO.OUT)
    GPIO.setup(AIN2, GPIO.OUT)
    GPIO.setup(PWMB, GPIO.OUT)
    GPIO.setup(BIN1, GPIO.OUT)
    GPIO.setup(BIN2, GPIO.OUT)

    pwmA = GPIO.PWM(PWMA, 50)
    pwmB = GPIO.PWM(PWMB, 50)

    pwmA.start(80)
    pwmB.start(80)

    while True:

        # ===== 停止 =====
        if direction == 360:
            GPIO.output(AIN1, 0)
            GPIO.output(AIN2, 0)
            GPIO.output(BIN1, 0)
            GPIO.output(BIN2, 0)

        # ===== 前進 =====
        elif direction == -360:
            GPIO.output(AIN1, 1)
            GPIO.output(AIN2, 0)
            GPIO.output(BIN1, 1)
            GPIO.output(BIN2, 0)

        # ===== 左回転 =====
        elif direction == 500:
            GPIO.output(AIN1, 1)
            GPIO.output(AIN2, 0)
            GPIO.output(BIN1, 0)
            GPIO.output(BIN2, 1)

        # ===== 右回転 =====
        elif direction == 600:
            GPIO.output(AIN1, 0)
            GPIO.output(AIN2, 1)
            GPIO.output(BIN1, 1)
            GPIO.output(BIN2, 0)

        # ===== 微調整（弱回転）=====
        elif direction > 0:
            GPIO.output(AIN1, 1)
            GPIO.output(AIN2, 0)
            GPIO.output(BIN1, 0)
            GPIO.output(BIN2, 1)

        elif direction < 0:
            GPIO.output(AIN1, 0)
            GPIO.output(AIN2, 1)
            GPIO.output(BIN1, 1)
            GPIO.output(BIN2, 0)

        time.sleep(0.05)
