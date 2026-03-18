import time

def run(state):
    print("[Phase2] Parachute Avoidance START")

    get_yaw = state["get_yaw"]
    get_distance = state["get_distance"]
    set_direction = state["set_direction"]

    SAFE_DISTANCE = 100   # cm
    SCAN_STEP = 30        # スキャン角度
    TURN_SPEED = 400
    ANGLE_TOL = 8         # 許容誤差（重要）

    scan_data = []

    # ===== スキャン =====
    print("[Phase2] Scanning...")

    start_yaw = get_yaw()

    for i in range(0, 360, SCAN_STEP):
        target_angle = (start_yaw + i) % 360

        # 回転（タイムアウト付き）
        rotate_start = time.time()
        while True:
            current = get_yaw()
            error = (target_angle - current + 540) % 360 - 180

            if abs(error) < ANGLE_TOL:
                break

            if time.time() - rotate_start > 3:
                print("[Phase2] Rotate Timeout")
                break

            if error > 0:
                set_direction(TURN_SPEED)
            else:
                set_direction(-TURN_SPEED)

        set_direction(360)
        time.sleep(0.2)

        # ===== 距離測定（強化版）=====
        values = []
        for _ in range(5):
            d = get_distance()
            if 0 < d < 400:
                values.append(d)
            time.sleep(0.03)

        if values:
            distance = sum(values) / len(values)
        else:
            distance = 400  # 最大値扱い

        scan_data.append((target_angle, distance))

        print(f"[Scan] angle={target_angle:.1f}, dist={distance:.1f}")

    # ===== 最適方向選択 =====
    best_angle = 0
    best_dist = -1

    for angle, dist in scan_data:
        if dist > best_dist:
            best_dist = dist
            best_angle = angle

    print(f"[Phase2] Best angle={best_angle:.1f}, dist={best_dist:.1f}")

    # ===== その方向へ向く =====
    rotate_start = time.time()
    while True:
        current = get_yaw()
        error = (best_angle - current + 540) % 360 - 180

        if abs(error) < ANGLE_TOL:
            break

        if time.time() - rotate_start > 5:
            print("[Phase2] Final Rotate Timeout")
            break

        if error > 0:
            set_direction(TURN_SPEED)
        else:
            set_direction(-TURN_SPEED)

    set_direction(360)
    time.sleep(0.3)

    # ===== 前進して離脱 =====
    print("[Phase2] Moving Forward")

    start_time = time.time()
    safe_count = 0

    while True:
        dist = get_distance()

        # 安全判定（連続判定）
        if dist > SAFE_DISTANCE:
            safe_count += 1
        else:
            safe_count = 0

        if safe_count > 5:
            print("[Phase2] Safe → Next Phase")
            set_direction(360)
            return 3

        # タイムアウト
        if time.time() - start_time > 6:
            print("[Phase2] Forward Timeout → Next Phase")
            set_direction(360)
            return 3

        set_direction(-360)  # 前進
        time.sleep(0.1)
