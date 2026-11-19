"""紅焰教學｜FFmpeg 影音縫合與卡拉 OK 逐字高亮字幕壓制腳本"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path.cwd()
PLAN = ROOT / 'scene-plan.json'
FINAL = ROOT / 'final_output.mp4'
TIMING = ROOT / 'dialogue-timing.json'
ASS = ROOT / 'subtitles.ass'

def probe(path):
    result = subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height',
        '-of', 'json', str(path),
    ], encoding='utf-8')
    info = json.loads(result)
    streams = info['streams']
    if {s['codec_type'] for s in streams} != {'video', 'audio'}:
        raise ValueError(f'Expected video and audio streams in {path.name}')
    video = next(s for s in streams if s['codec_type'] == 'video')
    if video['width'] * 16 != video['height'] * 9:
        raise ValueError(f'Expected a vertical 9:16 clip in {path.name}')
    return float(info['format']['duration'])

def timestamp(seconds):
    hundredths = max(0, round(seconds * 100))
    minutes, centiseconds = divmod(hundredths, 6000)
    hours, minute = divmod(minutes, 60)
    second, fraction = divmod(centiseconds, 100)
    return f'{hours}:{minute:02}:{second:02}.{fraction:02}'

def cue(start, end, text, style='Dialogue'):
    return f'Dialogue: 0,{timestamp(start)},{timestamp(end)},{style},,0,0,0,,{text}'

def split_caption(text):
    clauses = re.findall(r'[^，。；！？]+[，。；！？]*', text)
    lines = []
    line = ''
    for clause in clauses:
        if line and len(line + clause) > 20:
            lines.append(line)
            line = ''
        line += clause
    if line:
        lines.append(line)
    return lines

def extract_char_timings(scene_id, start, end):
    asr_path = ROOT / 'speech-review' / f'{scene_id}.json'
    if not asr_path.exists():
        return []
    asr = json.loads(asr_path.read_text(encoding='utf-8'))
    chars = []
    for seg in asr:
        for w_start, w_end, w_text in seg.get('words', []):
            if w_end <= start - 0.1 or w_start >= end + 0.1:
                continue
            tokens = re.findall(r'[\u4e00-\u9fffA-Za-z0-9]', w_text)
            if not tokens:
                continue
            ws = max(start, float(w_start))
            we = min(end, float(w_end))
            if we <= ws:
                we = ws + 0.05
            step = (we - ws) / len(tokens)
            for idx in range(len(tokens)):
                chars.append((ws + idx * step, ws + (idx + 1) * step))
    return chars


def build_karaoke_cues(offset, text, start, end, asr_chars):
    captions = split_caption(text)
    is_spoken = lambda ch: bool(re.match(r'[\u4e00-\u9fffA-Za-z0-9]', ch))
    total_spoken = sum(1 for cap in captions for ch in cap if is_spoken(ch))
    if total_spoken == 0:
        return [cue(offset + start, offset + end, text)]

    # Map each spoken character in the approved script to (c_start, c_end)
    char_spans = []
    if len(asr_chars) == total_spoken:
        char_spans = list(asr_chars)
    elif len(asr_chars) > 0:
        for i in range(total_spoken):
            a_idx = min(len(asr_chars) - 1, int(i * len(asr_chars) / total_spoken))
            b_idx = min(len(asr_chars) - 1, max(a_idx, int((i + 1) * len(asr_chars) / total_spoken) - 1))
            char_spans.append((asr_chars[a_idx][0], asr_chars[b_idx][1]))
    else:
        step = (end - start) / total_spoken
        char_spans = [(start + i * step, start + (i + 1) * step) for i in range(total_spoken)]

    # Build per-caption karaoke cues
    cues = []
    spoken_idx = 0
    for cap in captions:
        cap_count = sum(1 for ch in cap if is_spoken(ch))
        if cap_count == 0:
            continue
        cap_spans = char_spans[spoken_idx:spoken_idx + cap_count]
        spoken_idx += cap_count

        cap_start = cap_spans[0][0]
        cap_end = max(cap_spans[-1][1], cap_start + 0.2)

        parts = []
        cursor = cap_start
        local_i = 0
        for ch in cap:
            if is_spoken(ch):
                cs, ce = cap_spans[local_i]
                local_i += 1
                cs = max(cs, cursor)
                ce = max(ce, cs + 0.04)
                gap_cs = round((cs - cursor) * 100)
                if gap_cs > 0:
                    parts.append(f'{{\\k{gap_cs}}}')
                    cursor += gap_cs / 100.0
                dur_cs = max(2, round((ce - cursor) * 100))
                parts.append(f'{{\\kf{dur_cs}}}{ch}')
                cursor += dur_cs / 100.0
            else:
                parts.append(f'{{\\k0}}{ch}')

        cues.append(cue(offset + cap_start, offset + max(cap_end, cursor), ''.join(parts)))
    return cues


def assemble():
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    timing = json.loads(TIMING.read_text(encoding='utf-8'))
    files = [ROOT / 'clips' / f'{scene[0]}.mp4' for scene in plan]
    durations = [probe(path) for path in files]
    lines = [r'''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Dialogue,Microsoft JhengHei,54,&H0038D9FF,&H00FFFFFF,&H3010141B,&H3010141B,-1,0,0,0,100,100,0,0,3,11,0,2,72,130,240,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text''']
    offset = 0
    for scene, duration in zip(plan, durations):
        scene_id, _, _, shots = scene
        spoken_lines = [shot[3] for shot in shots if len(shot) == 4]
        ranges = timing[scene_id]
        if len(ranges) != len(spoken_lines):
            raise ValueError(f'Incomplete dialogue review in {scene_id}')
        previous_end = 0
        for text, (start, end) in zip(spoken_lines, ranges):
            if not previous_end <= start < end <= duration:
                raise ValueError(f'Invalid subtitle timing in {scene_id}: {start}, {end}')
            asr_chars = extract_char_timings(scene_id, start, end)
            lines.extend(build_karaoke_cues(offset, text, start, end, asr_chars))
            previous_end = end
        offset += duration
    ASS.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    inputs = [arg for path in files for arg in ('-i', str(path))]
    filters = []
    for index in range(len(files)):
        filters.append(f'[{index}:v]setsar=1,setpts=PTS-STARTPTS[v{index}]')
        filters.append(f'[{index}:a]aresample=48000,asetpts=PTS-STARTPTS[a{index}]')
    joined = ''.join(f'[v{i}][a{i}]' for i in range(len(files)))
    filters.append(f'{joined}concat=n={len(files)}:v=1:a=1[combined][aout]')
    filters.append('[combined]scale=1080:1920,ass=subtitles.ass[vout]')
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *inputs, '-filter_complex', ';'.join(filters),
        '-map', '[vout]', '-map', '[aout]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', str(FINAL),
    ], cwd=ROOT, check=True)
    print(f'{FINAL.name} {probe(FINAL):.2f}s')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='紅焰教學 FFmpeg 卡拉 OK 字幕成片合成工具')
    parser.add_argument('--project-dir', type=Path, default=Path.cwd(), help='專案目錄（內含 scene-plan.json、dialogue-timing.json、clips/、speech-review/）')
    parser.add_argument('--output', type=str, default='final_output.mp4', help='輸出檔名（相對或絕對路徑）')
    args = parser.parse_args()
    ROOT = args.project_dir.resolve()
    PLAN = ROOT / 'scene-plan.json'
    TIMING = ROOT / 'dialogue-timing.json'
    ASS = ROOT / 'subtitles.ass'
    out_path = Path(args.output)
    FINAL = out_path if out_path.is_absolute() else ROOT / out_path
    assemble()
