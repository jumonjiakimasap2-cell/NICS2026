import serial
import time
import math
import threading
import datetime
import csv
import RPi.GPIO as GPIO

import BNO055
import BMP085
import MicropyGPS

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
bmp = BMP085.BMP085()

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
# BMP180 平均化
# =====================
def get_altitude():
    values = []
    for _ in range(5):
        try:
            values.append(bmp.read_altitude())
        except:
            pass
        time.sleep(0.03)

    if values:
        return sum(values) / len(values)
    return 0

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
        current_alt = get_altitude()

        # 落下検知
        if fall > 25:
            fall_count += 1

        if fall_count >= 8 and landed_count >= 5:
            print("着地検知")
            time.sleep(5)
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
    global phase, motor_enabled

    print("Phase1: 特殊動作（右バック・左前進 5秒）")

    motor_enabled = False
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

    pwmA.start(70)
    pwmB.start(70)

    # ===== 動作 =====
    print("回転開始")

    # 右バック
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)

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

    print("Phase1終了")

    motor_enabled = True

    phase = 2

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.setup(HEATING_PIN, GPIO.OUT)

    bmx.setUp()

# =====================
# GPSスレッド
# =====================
def GPS_thread():
    global lat, lng, gps_detect

    s = serial.Serial("/dev/serial0", 115200)
    gps = MicropyGPS(9, "dd")

    while True:
        line = s.readline().decode("utf-8", errors="ignore")

        if len(line) < 10 or line[0] != "$":
            continue

        for c in line:
            gps.update(c)

        lat = gps.latitude[0]
        lng = gps.longitude[0]
        gps_detect = 1 if lat != 0 else 0

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

    threading.Thread(target=GPS_thread, daemon=True).start()
    threading.Thread(target=motor_thread, daemon=True).start()

    while True:
        if phase == 0:
            phase0()
        elif phase == 1:
            phase1()
        time.sleep(0.05)

if __name__ == "__main__":
    main()
