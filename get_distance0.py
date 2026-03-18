# -*- coding: utf-8 -*-
import math
import time
import RPi.GPIO as GPIO
import statistics
import BNO055

# =====================
# GPIO設定
# =====================
TRIG = 23
ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# =====================
# BNO055
# =====================
bno = BNO055.BNO055()
bno.setUp()

# =====================
# 距離取得（ノイズ除去）
# =====================
def get_distance():
    distances = []

    for _ in range(5):  # 複数回測定して中央値
        GPIO.output(TRIG, False)
        time.sleep(0.002)

        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        timeout = time.time()

        while GPIO.input(ECHO) == 0:
            start = time.time()
            if time.time() - timeout > 0.02:
                return 999

        timeout = time.time()
        while GPIO.input(ECHO) == 1:
            end = time.time()
            if time.time() - timeout > 0.02:
                return 999

        duration = end - start
        d = duration * 34300 / 2
        distances.append(d)

    return statistics.median(distances)


# =====================
# 方位角取得
# =====================
def get_yaw():
    mag = bno.getMag()
    yaw = 90 - (180 / 3.14159) * (0 if mag[0] == 0 else (math.atan2(mag[1], mag[0])))
    yaw %= 360
    return yaw


# =====================
# スキャン関数
# =====================
def scan_environment(set_direction_func):
    """
    set_direction_func(direction) を使ってモータ制御
    """

    scan_data = []

    start_angle = get_yaw()
    target_scan_range = 120  # ±60度
    step_angle = 10

    current_target = start_angle - target_scan_range / 2

    # 左端まで回転
    set_direction_func(-400.0)
    while abs((get_yaw() - current_target + 540) % 360 - 180) > 5:
        pass

    set_direction_func(360.0)
    time.sleep(0.2)

    # スキャン開始
    angle = current_target

    while angle <= start_angle + target_scan_range / 2:
        current_yaw = get_yaw()

        # 角度一致待ち
        if abs((current_yaw - angle + 540) % 360 - 180) < 5:
            d = get_distance()
            scan_data.append((current_yaw, d))
            print(f"[SCAN] angle={current_yaw:.1f}, dist={d:.1f}")

            angle += step_angle

        else:
            set_direction_func(-400.0)  # 微回転

    set_direction_func(360.0)

    return scan_data


# =====================
# コーン判定
# =====================
def detect_cone_like(scan_data):
    distances = [d for _, d in scan_data]

    if len(distances) < 3:
        return False, None

    avg = sum(distances) / len(distances)
    min_d = min(distances)

    # ① 周囲より近い
    if min_d > avg * 0.8:
        return False, None

    # ② 幅があるか（連続して近い）
    threshold = avg * 0.75

    cluster = []
    current = []

    for angle, d in scan_data:
        if d < threshold:
            current.append((angle, d))
        else:
            if len(current) >= 2:
                cluster.append(current)
            current = []

    if len(current) >= 2:
        cluster.append(current)

    if not cluster:
        return False, None

    # 最大クラスタ選択
    best_cluster = max(cluster, key=lambda x: len(x))

    # 中心角度
    angles = [a for a, _ in best_cluster]
    center_angle = sum(angles) / len(angles)

    return True, center_angle


# =====================
# メイン処理例
# =====================
def run(set_direction_func):
    while True:
        scan_data = scan_environment(set_direction_func)

        found, target_angle = detect_cone_like(scan_data)

        if found:
            print(f"[DETECTED] cone-like at {target_angle:.1f}")

            # 目標方向へ回転
            while True:
                yaw = get_yaw()
                diff = (target_angle - yaw + 540) % 360 - 180

                if abs(diff) < 5:
                    break

                if diff > 0:
                    set_direction_func(600.0)  # right
                else:
                    set_direction_func(500.0)  # left

            set_direction_func(-360.0)  # forward

            # 接近監視
            while True:
                d = get_distance()
                print(f"[APPROACH] {d:.1f} cm")

                if d < 20:
                    print("[GOAL]")
                    set_direction_func(360.0)
                    return

                time.sleep(0.1)

        else:
            print("[SEARCH] no object → rotate")
            set_direction_func(-400.0)
            time.sleep(0.5)
