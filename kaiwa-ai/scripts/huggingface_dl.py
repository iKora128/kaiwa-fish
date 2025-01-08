import os
import shutil
from huggingface_hub import hf_hub_download, snapshot_download

def download_repository(repo_id, local_dir):
    """リポジトリ全体をダウンロードし、シンボリックリンクを実ファイルに置き換える"""
    snapshot_download(repo_id=repo_id, local_dir=local_dir)
    replace_symlinks_with_files(local_dir)
    print(f"リポジトリ '{repo_id}' を '{local_dir}' にダウンロードし、シンボリックリンクを置換しました。")

def download_file(repo_id, filename, local_dir):
    """特定のファイルをダウンロードし、直接コピーする"""
    file_path = hf_hub_download(repo_id=repo_id, filename=filename)
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, filename)
    shutil.copy2(file_path, local_path)
    print(f"ファイル '{filename}' を '{local_path}' にコピーしました。")

def replace_symlinks_with_files(directory):
    """ディレクトリ内のシンボリックリンクを実ファイルに置き換える"""
    for root, dirs, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            if os.path.islink(file_path):
                real_path = os.path.realpath(file_path)
                os.remove(file_path)
                shutil.copy2(real_path, file_path)
                print(f"シンボリックリンク '{file_path}' を実際のファイルに置き換えました。")

if __name__ == "__main__":
    repo_id = "LiveTaro/nurudesasara"
    local_dir = "/home/nagashimadaichi/dev/kaiwa/models/tts/nurudesasara"

    # リポジトリ全体をダウンロード
    download_repository(repo_id, local_dir)

    # 特定のファイルをダウンロード（例として残しています）
    #filename = "riinu test_e100_s64000.safetensors"
    #download_file(repo_id, filename, local_dir)

    # ダウンロード後にシンボリックリンクを置換（念のため）
    #replace_symlinks_with_files(local_dir)