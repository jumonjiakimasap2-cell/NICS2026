# ===== フェーズ4内部状態 =====
phase4_state = "scan"
phase4_target_angle = None


def phase4():
    global direction
    global phase4_state, phase4_target_angle

    # =====================
    # ① スキャンフェーズ
    # =====================
    if phase4_state == "scan":
        print("=== Phase4: SCAN ===")

        scan_data = scan_environment(lambda d: set_direction(d))

        found, target_angle = detect_cone_like(scan_data)

        if found:
            print(f"[DETECTED] {target_angle:.1f}")
            phase4_target_angle = target_angle
            phase4_state = "align"
        else:
            print("[SEARCH] 見つからない → 回転")
            direction = -400.0

        return

    # =====================
    # ② 向き合わせ
    # =====================
    elif phase4_state == "align":
        yaw = get_yaw()
        diff = (phase4_target_angle - yaw + 540) % 360 - 180

        print(f"[ALIGN] diff={diff:.1f}")

        if abs(diff) < 5:
            print("[ALIGN OK]")
            phase4_state = "approach"
            return

        if diff > 0:
            direction = 600.0  # 右
        else:
            direction = 500.0  # 左

        return

    # =====================
    # ③ 接近フェーズ
    # =====================
    elif phase4_state == "approach":
        d = get_distance()
        print(f"[APPROACH] {d:.1f} cm")

        # 近すぎるなら停止（ゴール）
        if d < 20:
            print("🎯 GOAL（停止）")
            direction = 360.0
            return

        # 少しズレたら再調整
        yaw = get_yaw()
        diff = (phase4_target_angle - yaw + 540) % 360 - 180

        if abs(diff) > 10:
            print("[RE-ALIGN]")
            phase4_state = "align"
            return

        # 前進
        direction = -360.0
