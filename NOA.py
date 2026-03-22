import serial
import time
import math
import threading
import datetime
import csv
import RPi.GPIO as GPIO

import BNO055



# =====================
# GPIO
# =====================
TRIG = 23
ECHO = 24
HEATING_PIN = 17

# =====================
# センサ
# =====================
bmx = BNO055.BNO055()


# =====================
# 状態
# =====================
phase = 0
motor_enabled = True
direction = 360.0
gps_detect = 0

lat = 0.0
lng = 0.0
distance = 0.0
angle = 0.0
azimuth = 0.0
fall = 0.0
alt = 0.0


# =====================
# センサ
# =====================
def getBmxData():
    global fall
    acc = bmx.getAcc()
    fall = math.sqrt(acc[0]**2 + acc[1]**2 + acc[2]**2)

def calcAzimuth():
    global azimuth
    mag = bmx.getMag()
    azimuth = 90 - math.degrees(math.atan2(mag[1], mag[0]))
    azimuth *= -1
    azimuth %= 360

def calcDistanceAngle():
    global distance, angle
    R = 6378137.0

    dx = math.radians(TARGET_LNG - lng) * R * math.cos(math.radians(TARGET_LAT))
    dy = math.radians(TARGET_LAT - lat) * R

    distance = math.hypot(dx, dy)
    angle = 90 - math.degrees(math.atan2(dy, dx))
    angle %= 360

def get_yaw():
    calcAzimuth()
    return azimuth

def set_direction(val):
    global direction
    direction = val

def phase0():
    global phase

    start = time.time()
    fall_count = 0
    landed_count = 0

    print("Phase0: 落下検知")

    while True:
        getBmxData()

        # 落下検知
        if fall > 25:
            fall_count += 1

        if fall_count >= 8:
            print("着地検知")
            time.sleep(10)
            break

        if time.time() - start > 300:
            print("timeout")
            break

        time.sleep(0.05)

    phase = 1

# =====================
# Phase1
# =====================
def phase1():
    global phase,motor_enabled
    motor_enabled = False

    print("Phase1: 特殊動作（右バック・左前進 5秒）")

    time.sleep(0.1)  # ←超重要（競合防止）
    # ===== モーターピン =====
    PWMA = 18
    AIN1 = 8
    AIN2 = 25
    PWMB = 10
    BIN1 = 9
    BIN2 = 11

    # ===== 初期化（setupではなくここでやる）=====
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

    # ===== 動作 =====
    print("回転開始")

    # 右バック
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)

    # 左前進
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)

    time.sleep(5)

    # ===== 停止 =====
    print("停止")

    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.LOW)


    print("Phase1終了")

    phase = 2

def phase2():
    global phase,motor_enabled

    motor_enabled = False

    print("escape")

    PWMA = 18
    AIN1 = 8
    AIN2 = 25
    PWMB = 10
    BIN1 = 9
    BIN2 = 11

    pwmA = GPIO.PWM(PWMA, 50)
    pwmB = GPIO.PWM(PWMB, 50)

    pwmA.start(100)
    pwmB.start(100)

    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)

    # 左前進
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)

    time.sleep(5)

    # ===== 停止 =====
    print("停止")

    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.LOW)

    pwmA.stop()
    pwmB.stop()

    print("Phase2終了")

    phase = 3

    


def setup():
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.setup(HEATING_PIN, GPIO.OUT)

    bmx.setUp()



def motor_thread():
    global motor_enabled

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
       
        if not motor_enabled:
            time.sleep(0.05)
            continue

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

# =====================
# main
# =====================
def main():
    global phase

    setup()

    # threading.Thread(target=motor_thread, daemon=True).start()

    while True:
        if phase == 0:
            phase0()
        elif phase == 1:
            phase1()
        elif phase == 2:
            phase2()
        time.sleep(0.05)

if __name__ == "__main__":
    main()
