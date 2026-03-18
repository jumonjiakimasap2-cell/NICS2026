import math
import sys
import time
from pathlib import Path

import RPi.GPIO as GPIO  # ← 追加

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib import bno055, bmp180


# ====== HC-SR04設定 ======
TRIG = 23
ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)


def get_distance():
    # トリガー初期化
    GPIO.output(TRIG, False)
    time.sleep(0.05)

    # パルス送信
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    # 受信待ち
    start = time.time()
    while GPIO.input(ECHO) == 0:
        start = time.time()

    while GPIO.input(ECHO) == 1:
        stop = time.time()

    # 時間差から距離計算
    elapsed = stop - start
    distance = (elapsed * 34300) / 2  # cm

    return distance


def vec_norm(vec):
    values = [float(v) for v in vec[:3]]
    return math.sqrt(sum(v * v for v in values))


def main():
    print("Initializing BNO055...")
    bno = bno055.BNO055()
    bno_ok = bno.setUp()
    print(f"BNO055 setup: {bno_ok}")

    print("Initializing BMP180...")
    bmp = bmp180.BMP180(oss=3)
    bmp_ok = bmp.setUp()
    print(f"BMP180 setup: {bmp_ok}")

    print("Initializing HC-SR04...")
    hcsr04_ok = True  # GPIO動いてれば基本OK

    print("Stationary BNO accel norm should be near 9.8 m/s^2.")
    print("Indoor BMP pressure should be near 90000-105000 Pa.")
    print("HC-SR04 distance should be within 2cm - 400cm.")

    try:
        while True:
            now = time.strftime("%H:%M:%S")

            # ===== BNO =====
            if bno_ok:
                acc = bno.getAcc()
                gyro = bno.getGyro()
                mag = bno.getMag()
                euler = bno.getEuler()
                sys_status = bno.getSystemStatus()
                sys_error = bno.getSystemError()
                calib = bno.getCalibrationStatus()

                if acc["valid"] and gyro["valid"] and mag["valid"] and euler["valid"]:
                    print(
                        f"[{now}] BNO "
                        f"|acc|={vec_norm(acc['value']):.2f} "
                        f"|gyro|={vec_norm(gyro['value']):.2f} "
                        f"|mag|={vec_norm(mag['value']):.2f} "
                        f"euler={euler['value']} calib={calib}"
                    )
                else:
                    print(f"[{now}] BNO invalid")
            else:
                print(f"[{now}] BNO unavailable")

            # ===== BMP =====
            if bmp_ok:
                temp = bmp.getTemperature()
                pres = bmp.getPressure()
                alt = 44330.0 * (1.0 - math.pow(float(pres) / 101325.0, 1.0 / 5.255))
                print(f"[{now}] BMP temp={float(temp):.2f}C pres={float(pres):.2f}Pa alt={alt:.2f}m")
            else:
                print(f"[{now}] BMP unavailable")

            # ===== HC-SR04 =====
            if hcsr04_ok:
                try:
                    dist = get_distance()
                    if 2 <= dist <= 400:
                        print(f"[{now}] SONAR distance={dist:.2f} cm")
                    else:
                        print(f"[{now}] SONAR out of range: {dist:.2f} cm")
                except Exception as e:
                    print(f"[{now}] SONAR error: {e}")
            else:
                print(f"[{now}] SONAR unavailable")

            print("-" * 50)
            time.sleep(1.0)

    except KeyboardInterrupt:
        print("Stopping...")
        GPIO.cleanup()


if __name__ == "__main__":
    main()
