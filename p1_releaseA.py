import RPi.GPIO as GPIO
import time

HEATING_PIN = 26

def run(state):
    print("[Phase1] Parachute Release Start")

    # GPIO初期化（すでにやってる場合はスキップしてもOK）
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(HEATING_PIN, GPIO.OUT)

    try:
        print("[Phase1] Heating wire ON")

        GPIO.output(HEATING_PIN, GPIO.HIGH)

        # 元コード参考（7秒でもOK、ここは調整ポイント）
        duration = state.get("heating_time", 5)
        time.sleep(duration)

        GPIO.output(HEATING_PIN, GPIO.LOW)

        print("[Phase1] Heating wire OFF")
        print("[Phase1] Parachute Released")

        # 次のフェーズへ
        return 2

    except Exception as e:
        print("[Phase1] ERROR:", e)

        GPIO.output(HEATING_PIN, GPIO.LOW)
        return 1  # リトライ
