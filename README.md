# NICS2026

1. 環境構築の準備
ハードウェア
Raspberry Pi Zero 2 W
microSDカード（16GB以上あれば良い）
電源（5V / 2.5A）（PCからのUSB給電でもよいが、不安定になるときがある）
PC
モニター・キーボード・USBハブ（あると便利）
Mini HDMI ケーブル（モニター接続用）
ソフトウェア
Raspberry Pi Imager
Git
ターミナル
WSL2（Windowsユーザーは推奨）
2. Raspberry Pi Zero 2 W のセットアップ
2.1 OS イメージの準備
Raspberry Pi Imager をインストールする（ https://www.raspberrypi.com/software/ ）

起動後、

Device → Raspberry Pi Zero 2 W
OS → Raspberry Pi OS(other)からRaspberry Pi OS Lite（64-bit） （GUIは要らない）
Storage → MicroSDカード
以下を設定・有効化する

Hostname
Localisation（国・キーボード設定）
User
Wi-Fi
Remote access（SSHの有効化、パスワード認証で十分）
Raspberry Pi Connect（オフでよい）
Writing（書き込み）を実行

2.2 初回起動と接続
microSD を ラズパイ に挿入して電源投入

PC から次のコマンドで接続

ssh ユーザー名@ホスト名.local（or IPアドレス）
パスワードは Imager で設定したものを使用

2.3 接続できない場合は以下を確認
同一ネットワークにいるか

.local 解決ができない環境では、ラズパイの IPアドレス を確認して、ホスト名のところを IP に置き換えて接続する（WindowsやAndroid端末では、mDNS（.local）が安定的にサポートされておらず、ホスト名接続は一般に不安定）

Permission denied (publickey,password).が出る場合、以下のコマンドで接続

ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no ユーザー名@IPアドレス
その後、以下のコマンドでラズパイ上の設定を確認

sudo nano /etc/ssh/sshd_config
その中に、以下の行があれば確認。

PasswordAuthentication yes
PasswordAuthentication が no になっていたら yes に変更。

"#" でコメントアウトされている場合は、"#" を外して PasswordAuthentication yes にする

設定を変更したら、SSH サーバーを再起動。

sudo systemctl restart ssh
2.3 初期アップデート
sudo apt update
sudo apt full-upgrade -y
sudo reboot
3. Python 実行環境の構築
3.1 依存パッケージのインストール
# ===== 基本ツール =====
sudo apt install -y git tmux i2c-tools

# ===== 実行に必要なPythonライブラリ（apt）=====
# GPIO / シリアル / I2C
sudo apt install -y python3-gpiozero python3-rpi-lgpio liblgpio1 python3-serial python3-smbus

# pipでライブラリを追加インストールするためのツール
sudo apt install -y python3-pip python3-setuptools

# カメラ / 画像処理（Picamera2 + OpenCV + NumPy）
sudo apt install -y python3-picamera2 python3-libcamera libcamera-apps python3-opencv python3-numpy

# OpenCVでGUI表示（imshow等）する場合に必要。ヘッドレス運用なら不要なことが多い
sudo apt install -y libgl1

# ===== ここから下は自前ビルドをするなら必要=====

# C拡張やライブラリをソースからビルドする場合に必要
# sudo apt install -y build-essential python3-dev swig

# lgpio を C で開発/コンパイルする場合のヘッダ（Pythonで動かすだけなら通常不要）
# sudo apt install -y liblgpio-dev
3.2 Python 仮想環境の作成
# 仮想環境の作成（システムパッケージを引き継ぐ --system-site-packages が重要）
# これにより、aptで入れた OpenCV や Picamera2 などがそのまま仮想環境内でも使用可能になる
python3 -m venv --system-site-packages venv

# 仮想環境の有効化
source venv/bin/activate

# pip自体の更新
pip install --upgrade pip

# GPS解析用ライブラリ
pip install pynmea2

# その他、main.py等で必要なライブラリがあればここで追加
# pip install smbus2
4. シリアル通信 / GPIO / I2C の有効化
4.1 raspi-config での設定
sudo raspi-config
4.2 以下を有効化
Interface Options → I2C
Interface Options → Serial
完了後、再起動。

sudo reboot
5. リポジトリのクローン
git clone https://github.com/jumonjiakimasap2/NICS2026
cd NICS2026
