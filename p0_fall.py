def phase0_fall_detection():
    """
    フェーズ0：落下検知フェーズ
    BMXから加速度を取得して落下を判断する
    """
    global phase
    start = time.time()
    fall_count = 0

    print("phase0 : falling")

    while True:
        getBmxData()  # 加速度・ジャイロ・磁気データを取得
        if fall > 25:  # 落下判定
            fall_count += 1
            print("fall_count:", fall_count)
            if fall_count >= 8:  # 連続して落下を検知
                print("para released")
                time.sleep(10)  # パラシュート解放待ち
                break

        # タイムアウト（落下検知に失敗した場合）
        if time.time() - start > 7*60:
            print("failed to detect falling")
            break

        time.sleep(0.01)

    phase = 1  # フェーズ1へ移行
