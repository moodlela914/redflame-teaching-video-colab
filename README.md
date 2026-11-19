# 紅焰教學｜AI 科普與情境短劇影音工作流 Skill（v2.0）

> **技能名稱**：`redflame-teaching-video-colab`  
> **適用平台**：Codex / Antigravity / Claude Code / Gemini CLI 等支援 `SKILL.md` 之 AI Agent 環境

一套經過實戰打磨的端到端 **9:16 / 16:9 AI 科普與情境短劇影音製作 Skill**。結合 **Google Colab（MiniMax H3 Ref2VA）**、**Faster-Whisper 逐字語音品管** 與 **FFmpeg 卡拉 OK 逐字高亮字幕壓制**，專為「一次成型、減少中途返工」設計。

---

## 核心特色與防返工鐵則

1. **先審分鏡再動 GPU**：推論前先核對臺灣現行法規／知識內容並提交分鏡表，確認後才分配 Colab GPU，批次結束自動停機（`--stop-on-complete`）。
2. **角色隔離防變臉換裝**：每鏡 `subject_definitions` 僅描述該幕實際出場角色；雙人鏡頭鎖定左右位置、服裝與眼鏡，杜絕中途變身。
3. **相鄰鏡頭防跳幀**：相鄰兩鏡交錯景別（單人近景 ↔ 雙人中景 ↔ 特寫反打），轉場自然流暢。
4. **嚴禁 AI 亂碼字牌**：提示詞全面禁用 `card` / `board` / `sign` 等誘導字，杜絕模型幻覺生成亂碼看板。
5. **Whisper 自動抓英文漏讀與口糊**：依臺灣華語 4 字／秒精準排秒，內建 `review_speech.py` 自動偵測 `[A-Za-z]` 異常英文漏讀。
6. **純底部卡拉 OK 逐字高亮字幕**：拔除畫面上方突兀字卡，以 Whisper 逐字時間戳 1:1 對應繁中台詞，透過 `assemble_karaoke.py` 產出 ASS `\kf` 白轉金（`#FFD938`）平滑掃描字幕。

---

## 套件結構

```text
redflame-teaching-video-colab/
├── SKILL.md                                  # 紅焰教學影音工作流主規範
├── README.md                                 # 專案說明文件
├── assets/
│   └── MiniMax_H3_Turbo_Portrait.ipynb       # Colab 9:16 直式（576×1024）推論筆記本
├── scripts/
│   ├── runner.py                             # Colab CLI 工作階段與批次推論控制器
│   ├── review_speech.py                      # Faster-Whisper 逐字辨識與英文漏讀警報
│   └── assemble_karaoke.py                   # FFmpeg 影音縫合與卡拉 OK 字幕壓制腳本
└── references/
    ├── one-shot-prompt-template.md           # 七大類一次成型免修改提示詞範本
    └── pitfalls-and-qa-checklist.md          # 實戰五大踩坑對策與交付驗收清單
```

---

## 快速安裝與使用

### 1. 安裝 Skill
將本儲存庫複製至您的 Agent 技能目錄（例如 `~/.codex/skills/` 或 `~/.gemini/config/skills/`）：

```bash
git clone https://github.com/moodlela914/redflame-teaching-video-colab.git
```

### 2. 前置環境準備
* **Google Colab**：登入 [Google Colab](https://colab.research.google.com/) 並備妥 A100 運算單位（[方案頁](https://colab.research.google.com/signup)）。
* **Colab CLI**：`uv tool install google-colab-cli` 並執行 `colab login`。
* **本機後製工具**：[FFmpeg](https://ffmpeg.org/)（含 `libass`）與 [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)。

### 3. 常用指令
```powershell
# 查詢 Colab 運算單位餘額
python scripts/runner.py usage --json

# 批次生成影片並於完成後自動停止 GPU
python scripts/runner.py batch --manifest jobs.json --gpu A100 --no-high-mem --stop-on-complete --timeout 2400

# Whisper 逐字語音驗收（偵測英文漏讀即報警）
python scripts/review_speech.py clips/01-office.mp4

# 合成 1080×1920 含卡拉 OK 逐字高亮字幕成片
python scripts/assemble_karaoke.py --project-dir . --output final_output.mp4
```

---

## 相關官方資源

* [Google Colab](https://colab.research.google.com/) ｜ [google-colab-cli (PyPI)](https://pypi.org/project/google-colab-cli/)
* [Comfy-Org / MiniMax-H3 (Hugging Face)](https://huggingface.co/Comfy-Org/MiniMax-H3) ｜ [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
* [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) ｜ [FFmpeg](https://ffmpeg.org/)

---

## 授權條款（License）

本 Skill 程式碼與文件採 [MIT License](LICENSE) 授權；推論所呼叫之第三方模型與工具（如 MiniMax H3、ComfyUI、Faster-Whisper、FFmpeg 等）各依其上游官方授權條款辦理。
