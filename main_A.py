# main.py
import time
import RPi.GPIO as GPIO

# フェーズモジュール
import p0_fall as phase0
import p1_releaseA as phase1
import p2_dispara as phase2
import p3_run as phase3
import p4_goal as phase4

# グローバル変数
lat = 0.0
lng = 0.0
direction = 0.0
phase = 0

# モーター・センサー関数をstateに登録
def get_yaw():
    return 0.0

def get_distance():
    return 200.0

def set_direction_fn(value):
    global direction
    direction = value

def main(init_lat=0.0, init_lng=0.0):
    global lat, lng, phase, direction

    lat = init_lat
    lng = init_lng

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    state = {
        "lat": lat,
        "lng": lng,
        "get_yaw": get_yaw,
        "get_distance": get_distance,
        "set_direction": set_direction_fn,
        "heating_time": 5,
    }

 # フェーズ制御
phase = 0

# フェーズ0
print("=== Phase0 ===")
phase = phase0.phase0_fall_detection(state)  # 内部で正常終了するまでリトライ

# フェーズ1
print("=== Phase1 ===")
phase = phase1.run(state)  # run 内で失敗時に return 1 でリトライする場合は run 内に while を作るとよい

# フェーズ2,3,4
print("=== Phase2 ===")
phase = phase2.run(state)

print("=== Phase3 ===")
phase3.phase3()

print("=== Phase4 ===")
phase4.phase4()
