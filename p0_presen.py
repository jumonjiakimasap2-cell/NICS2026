# phase0_runner.py
import time
import pandas as pd
from pathlib import Path
import sensor
import log

def phase0_run(state, duration_sec: float = 60.0, interval: float = 1.0):
    """
    フェーズ0: センサー値を取得してログに保存
    state: dict形式の状態オブジェクト（必要なら次フェーズ情報を保持）
    duration_sec: 実行時間（秒）
    interval: 取得間隔（秒）
    """
    while True:  # 正常終了するまで繰り返す
        try:
            start_time = time.time()
            records = []

            out_dir = Path("phase0_logs")
            out_dir.mkdir(exist_ok=True)
            state["out_dir"] = out_dir

            print("[Phase0] Starting sensor logging...")

            while (time.time() - start_time) < duration_sec:
                now = time.time() - start_time
                timestamp = pd.Timestamp.now()

                # ===== BNO =====
                bno_data = {}
                bno = sensor.bno055.BNO055()
                if bno.setUp():
                    acc = bno.getAcc()
                    gyro = bno.getGyro()
                    mag = bno.getMag()
                    bno_data = {
                        "AccX": acc["value"][0],
                        "AccY": acc["value"][1],
                        "AccZ": acc["value"][2],
                        "GyroX": gyro["value"][0],
                        "GyroY": gyro["value"][1],
                        "GyroZ": gyro["value"][2],
                        "MagX": mag["value"][0],
                        "MagY": mag["value"][1],
                        "MagZ": mag["value"][2],
                    }

                # ===== BMP =====
                bmp_data = {}
                bmp = sensor.bmp180.BMP180(oss=3)
                if bmp.setUp():
                    pres = bmp.getPressure()
                    alt = 44330.0 * (1.0 - (pres / 101325.0) ** (1/5.255))
                    bmp_data = {"ALT": alt, "Pres": pres}

                # ===== HC-SR04 =====
                dist_data = {}
                try:
                    dist = sensor.get_distance()
                    dist_data = {"ObstacleDist": dist}
                except Exception:
                    dist_data = {"ObstacleDist": None}

                # レコードまとめ
                record = {"ElapsedSec": now, "Phase": 0, "Timestamp": timestamp}
                record.update(bno_data)
                record.update(bmp_data)
                record.update(dist_data)
                records.append(record)

                print(f"[Phase0] {timestamp} | Distance={dist_data.get('ObstacleDist',0):.2f} cm | ALT={bmp_data.get('ALT',0):.2f} m")
                time.sleep(interval)

            # データフレーム化
            df = pd.DataFrame(records)

            # 出力ディレクトリ準備
            log_out_dir = log.prepare_output_dir(Path(out_dir))
            csv_path = log_out_dir / "phase0_sensor_log.csv"
            df.to_csv(csv_path, index=False)
            print(f"[Phase0] Log saved to {csv_path}")

            # anomaly detection
            df = log.detect_anomalies(df, log_out_dir)

            # 状態オブジェクトに保存
            state["df_phase0"] = df
            state["phase0_out_dir"] = log_out_dir

            print("[Phase0] Completed successfully.")
            return 1  # 次のフェーズ番号を返す

        except Exception as e:
            print(f"[Phase0] ERROR: {e}")
            print("[Phase0] Retrying phase0...")
            time.sleep(2.0)  # リトライ前に少し待機
