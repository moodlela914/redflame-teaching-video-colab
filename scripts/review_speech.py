"""紅焰教學｜Faster-Whisper 逐字語音辨識與英文漏讀檢查腳本"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

MODEL = 'base'


def speech(path, model):
    audio = subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', str(path), '-vn', '-ac', '1',
        '-ar', '16000', '-f', 'f32le', '-',
    ])
    segments, _ = model.transcribe(
        np.frombuffer(audio, dtype=np.float32),
        language='zh', beam_size=5, word_timestamps=True, condition_on_previous_text=False,
    )
    return [
        {
            'start': round(segment.start, 2),
            'end': round(segment.end, 2),
            'text': segment.text,
            'words': [[round(word.start, 2), round(word.end, 2), word.word] for word in segment.words],
        }
        for segment in segments
    ]


def main():
    if len(sys.argv) > 1:
        sources = [Path(arg).resolve() for arg in sys.argv[1:]]
        review_dir = sources[0].parent.parent / 'speech-review'
    else:
        cwd = Path.cwd()
        sources = sorted((cwd / 'clips').glob('*.mp4'))
        review_dir = cwd / 'speech-review'

    review_dir.mkdir(exist_ok=True)
    model = WhisperModel(MODEL, device='cpu', compute_type='int8', local_files_only=True)
    has_warning = False

    for path in sources:
        data = speech(path, model)
        (review_dir / f'{path.stem}.json').write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8',
        )
        for segment in data:
            text = segment['text']
            eng = re.findall(r'[A-Za-z]+', text)
            flag = f'  [WARNING: 偵測到英文漏讀 {eng}]' if eng else ''
            if eng:
                has_warning = True
            print(f"{path.stem} {segment['start']:5.2f}–{segment['end']:5.2f} {text}{flag}")

    if has_warning:
        sys.exit(2)


if __name__ == '__main__':
    main()
