import serial
import time
import math
import threading
import datetime
import csv
import RPi.GPIO as GPIO

import BNO055
import BMP085
import micropyGPS

# =====================
# GPIO
# =====================
TRIG = 23
ECHO = 24
HEATING_PIN = 26

# =====================
# 目標
# =====================
TARGET_LAT = 30.374239
TARGET_LNG = 130.959967

# =====================
# センサ
# =====================
bmx = BNO055.BNO055()
bmp = BMP085.BMP085()

# =====================
# 状態
# =====================
phase = 0
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
# HC-SR04（安全版）
# =====================
def get_distance():
    GPIO.output(TRIG, False)
    time.sleep(0.002)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    timeout = time.time()

    while GPIO.input(ECHO) == 0:
        if time.time() - timeout > 0.02:
            return 400

    start = time.time()

    while GPIO.input(ECHO) == 1:
        if time.time() - start > 0.02:
            return 400

    stop = time.time()
    dist = (stop - start) * 34300 / 2
    return dist

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

# =====================
# Phase0（改良版）
# =====================
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

        # 着地検知（気圧）
        if current_alt < 5:
            landed_count += 1

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
    global phase

    print("Phase1: パラ分離")

    GPIO.output(HEATING_PIN, GPIO.HIGH)
    time.sleep(3)
    GPIO.output(HEATING_PIN, GPIO.LOW)

    phase = 2

# =====================
# Phase2（完全）
# =====================
def phase2():
    global phase

    SAFE_DISTANCE = 100
    SCAN_STEP = 30
    TURN_SPEED = 400
    ANGLE_TOL = 8

    scan_data = []
    start_yaw = get_yaw()

    print("Phase2: 回避")

    for i in range(0, 360, SCAN_STEP):
        target = (start_yaw + i) % 360

        while True:
            current = get_yaw()
            error = (target - current + 540) % 360 - 180

            if abs(error) < ANGLE_TOL:
                break

            set_direction(TURN_SPEED if error > 0 else -TURN_SPEED)

        set_direction(360)
        time.sleep(0.2)

        vals = [get_distance() for _ in range(5)]
        dist = sum(vals)/len(vals)

        scan_data.append((target, dist))

    best_angle = max(scan_data, key=lambda x: x[1])[0]

    while True:
        current = get_yaw()
        error = (best_angle - current + 540) % 360 - 180

        if abs(error) < ANGLE_TOL:
            break

        set_direction(TURN_SPEED if error > 0 else -TURN_SPEED)

    set_direction(360)

    start = time.time()
    safe_count = 0

    while True:
        d = get_distance()

        if d > SAFE_DISTANCE:
            safe_count += 1
        else:
            safe_count = 0

        if safe_count > 5 or time.time() - start > 6:
            phase = 3
            return

        set_direction(-360)
        time.sleep(0.1)

# =====================
# Phase3（GPS）
# =====================
def phase3():
    global phase, direction

    if gps_detect == 0:
        direction = 360
        return

    calcAzimuth()
    calcDistanceAngle()

    print(f"距離:{distance:.2f}")

    if distance < 5:
        phase = 4
        return

    diff = (azimuth - angle + 540) % 360 - 180

    if abs(diff) < 10:
        direction = -360
    elif diff > 0:
        direction = 500
    else:
        direction = 600

# =====================
# Phase4（最終接近）
# =====================
phase4_state = "scan"
phase4_target = 0

def phase4():
    global phase4_state, phase4_target, direction

    if phase4_state == "scan":
        data = []

        for _ in range(12):
            set_direction(400)
            time.sleep(0.2)
            data.append((get_yaw(), get_distance()))

        phase4_target = min(data, key=lambda x: x[1])[0]
        phase4_state = "align"

    elif phase4_state == "align":
        diff = (phase4_target - get_yaw() + 540) % 360 - 180

        if abs(diff) < 5:
            phase4_state = "approach"
        else:
            direction = 600 if diff > 0 else 500

    elif phase4_state == "approach":
        d = get_distance()

        if d < 20:
            print("GOAL")
            direction = 360
            return

        direction = -360

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

# =====================
# モータ（ダミー）
# =====================
def motor_thread():
    global direction
    while True:
        print("DIR:", direction)
        time.sleep(0.1)

# =====================
# Setup
# =====================
def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.setup(HEATING_PIN, GPIO.OUT)

    bmx.setUp()

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
        elif phase == 2:
            phase2()
        elif phase == 3:
            phase3()
        elif phase == 4:
            phase4()

        time.sleep(0.05)

if __name__ == "__main__":
    main()
