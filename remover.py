import torch
import librosa
import soundfile as sf
import numpy as np
from utils import get_model_from_config, demix

def bgm_remove(
    input_path: str,
    output_path: str,
    model_type: str = 'mel_band_roformer',
    config_path: str = 'configs/config_vocals_mel_band_roformer_kim.yaml',
    checkpoint_path: str = 'models/MelBandRoformer.ckpt',
    sample_rate: int = 44100,
) -> None:
    """
    音声ファイルからボーカルを除去する関数
    
    Args:
        input_path: 入力音声ファイルのパス
        output_path: 出力音声ファイルのパス
        model_type: モデルタイプ（デフォルト: 'mel_band_roformer'）
        config_path: 設定ファイルのパス（デフォルト: 'config_vocals_mel_band_roformer_kim.yaml'）
        checkpoint_path: モデルチェックポイントのパス（デフォルト: 'MelBandRoformer.ckpt'）
        sample_rate: サンプルレート（デフォルト: 44100）
    """
    # デバイスの設定
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # モデルの読み込み
    model, config = get_model_from_config(model_type, config_path)
    if checkpoint_path:
        state_dict = torch.load(checkpoint_path, map_location=device)
        if 'state' in state_dict:
            state_dict = state_dict['state']
        if 'state_dict' in state_dict:
            state_dict = state_dict['state_dict']
        model.load_state_dict(state_dict)
    
    model = model.to(device)
    model.eval()
    
    # 音声の読み込み
    try:
        mix, sr = librosa.load(input_path, sr=sample_rate, mono=False)
    except Exception as e:
        raise Exception(f'Cannot read track: {input_path}. Error: {str(e)}')
    
    # モノラルをステレオに変換
    if len(mix.shape) == 1:
        mix = np.stack([mix, mix], axis=0)
    
    mix_orig = mix.copy()
    
    # 音声の分離処理
    waveforms = demix(config, model, mix, device)
    
    # ボーカルを除去した音声（インストゥルメンタル）を取得
    if 'vocals' in waveforms:
        instrumental = mix_orig - waveforms['vocals']
    else:
        raise Exception("Vocals stem not found in model output")
    
    # 結果の保存
    sf.write(output_path, instrumental.T, sample_rate, subtype='FLOAT')

# 使用例
if __name__ == "__main__":
    bgm_remove(
        input_path="path/to/input.wav",
        output_path="path/to/output.wav",
        model_type="mel_band_roformer",
        config_path="configs/config_vocals_mel_band_roformer_kim.yaml",
        checkpoint_path="models/MelBandRoformer.ckpt"
    ) 