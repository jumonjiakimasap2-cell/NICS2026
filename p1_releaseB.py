import time
import RPi.GPIO as GPIO

# ピン定義（元コードと同じ）
PWMA = 18
AIN1 = 8
AIN2 = 25
PWMB = 10
BIN1 = 9
BIN2 = 11

def setup_motor():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(PWMA, GPIO.OUT)
    GPIO.setup(AIN1, GPIO.OUT)
    GPIO.setup(AIN2, GPIO.OUT)
    GPIO.setup(PWMB, GPIO.OUT)
    GPIO.setup(BIN1, GPIO.OUT)
    GPIO.setup(BIN2, GPIO.OUT)

    pwmA = GPIO.PWM(PWMA, 50)
    pwmB = GPIO.PWM(PWMB, 50)

    pwmA.start(100)
    pwmB.start(100)

    return pwmA, pwmB


def stop():
    GPIO.output(AIN1, LOW)
    GPIO.output(AIN2, LOW)
    GPIO.output(BIN1, LOW)
    GPIO.output(BIN2, LOW)


def spin_right():  # 右前・左後（その場回転）
    # 右前
    GPIO.output(AIN1, HIGH)
    GPIO.output(AIN2, LOW)

    # 左後
    GPIO.output(BIN1, LOW)
    GPIO.output(BIN2, HIGH)


def spin_left():  # 右後・左前
    # 右後
    GPIO.output(AIN1, LOW)
    GPIO.output(AIN2, HIGH)

    # 左前
    GPIO.output(BIN1, HIGH)
    GPIO.output(BIN2, LOW)


def forward():
    GPIO.output(AIN1, HIGH)
    GPIO.output(AIN2, LOW)
    GPIO.output(BIN1, HIGH)
    GPIO.output(BIN2, LOW)


def run():
    print("[Phase1] Direct Motor Control Start")

    pwmA, pwmB = setup_motor()

    try:
        # 🔥 ① スピン（パラ離脱）
        spin_left()
        time.sleep(5)

        # 🔥 ② 前進
        forward()
        time.sleep(2)

        # 🔥 ③ 停止
        stop()

        print("[Phase1] Done")

    except Exception as e:
        print("[Phase1] ERROR:", e)
        stop()

    finally:
        GPIO.cleanup()
            # ③ 停止
        direction = 360.0

        print("[Phase1] Escape Complete")

        return 2  # 次のフェーズへ
