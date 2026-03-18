def phase3():
    global direction, gps_detect, phase
    global azimuth, angle, distance

    # ===== GPS未取得なら停止 =====
    if gps_detect == 0:
        print("GPS待機中...")
        direction = 360.0
        return

    # ===== センサ取得（ここ重要）=====
    getBmxData()      # ← BNO055
    calcAzimuth()     # ← 方位

    calcAngle()       # ← GPS使って角度
    calcdistance()    # ← GPS使って距離

    # ===== ログ =====
    print(f"[GPS] lat:{lat}, lng:{lng}")
    print(f"[距離] {distance:.2f} m")
    print(f"[角度] {angle:.1f}")
    print(f"[方位] {azimuth:.1f}")

    # ===== フェーズ遷移 =====
    if distance < 5.0:
        print("🎯 Phase4へ")
        direction = 360.0
        phase = 4
        return

    # ===== 方向制御 =====
    diff = azimuth - angle
    diff %= 360

    if diff > 180:
        diff -= 360

    print(f"[差分] {diff:.1f}")

    # ===== モータ指令 =====
    if abs(diff) < 10:
        direction = -360.0  # 前進

    elif diff > 45:
        direction = 500.0   # 強左

    elif diff > 0:
        direction = diff    # 弱左

    elif diff < -45:
        direction = 600.0   # 強右

    else:
        direction = diff    # 弱右
