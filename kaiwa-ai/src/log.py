## log.py

import logging
import inspect
import os
from datetime import datetime

def setup_logging():
    # スクリプトのあるディレクトリを取得
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 現在の日時を取得して、ファイル名に使用
    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    # ログディレクトリのパスを設定
    log_directory = os.path.join(script_dir, 'logs')
    log_filename = os.path.join(log_directory, f'app_{current_time}.log')

    # ログディレクトリが存在しない場合は作成
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # ログファイルの設定
    fh = logging.FileHandler(log_filename, mode='a', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(fh)

    # コンソール出力用ハンドラーも追加
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def log_error():
    # 現在のスタックフレームを取得
    func = inspect.currentframe().f_back.f_code
    # 関数名とエラーメッセージをログに記録
    logging.error(f"Error in {func.co_name}: An error occurred.")