---
name: redflame-teaching-video-colab
description: 紅焰教學 AI 科普與情境短劇影音工作流（Colab MiniMax H3 9:16／16:9 全流程）。涵蓋前置法規與知識查核、防漂移分鏡設計、角色與服裝鎖定、Colab A100 批次生成、Whisper 逐字語音驗收（防英文漏讀與口糊）與純底部卡拉 OK 逐字高亮繁中字幕合成。適用紅焰教學科普短片、法律／教育情境對話短劇與端到端多鏡製片。
---

# 紅焰教學｜AI 科普與情境短劇影音工作流（Colab H3 v2.0）

本技能整合 **紅焰教學** 實戰驗證過的端到端 AI 短影音製片流程，專為「一次成型、減少中途返工」設計。透過 Google Colab CLI 驅動 MiniMax H3（Ref2VA），結合本機 Faster-Whisper 逐字語音驗收與 FFmpeg 卡拉 OK 字幕壓制，穩定產出高品質直式（9:16）或橫式（16:9）科普與情境短片。

## 一、核心製作鐵則（防返工紅線）

除非使用者在當次任務明確指定其他配置，製作全程嚴格遵循以下規範：

1. **先審分鏡再動 GPU**：啟動影片推論或分配 Colab GPU 前，必須先提交完整分鏡表（各幕情節、秒數、景別、參考圖、人物位置、動作、核定繁中台詞），取得使用者確認後再執行。同一任務已核准之分鏡沿用不重複確認。
2. **知識／法規內容先行查核**：凡涉及法律、醫療、稅務或官方政策之科普腳本，必須先查核臺灣現行法規與官方案例，校正不精確口語（例如避免過度武斷之要件描述），再鎖定台詞。
3. **角色隔離原則（防變臉與換裝漂移）**：
   - **每鏡的 `subject_definitions` 只能寫「該鏡頭畫面裡實際出現的角色」**，未出場角色嚴禁寫進該鏡提示詞。
   - 雙人鏡頭必須明確寫出 `LEFT` / `RIGHT` 位置、服裝、髮型與是否有眼鏡（如 `no glasses`），切鏡時加上 `Continuous uncut take, maintain both original faces and original clothes without changing identity, hairstyle, glasses or outfits`。
4. **相鄰鏡頭禁同構圖（防跳幀）**：相鄰兩鏡嚴禁使用同一張參考圖與相同景別硬切；須交錯「近景 ↔ 雙人中景 ↔ 特寫反打」，確保轉場自然流暢。
5. **嚴禁誘導模型生成畫面文字（防 AI 亂碼看板）**：
   - 提示詞中**絕對不可出現** `card`、`information card`、`board`、`sign`、`title`、`overlay` 等誘導詞（即使是「預留字卡空間」也不行）。
   - 一律寫死 `Absolutely no generated text, signs, boards, placards, cards, subtitles or overlays anywhere in the video`。
6. **字數與秒數精準配比（防英文漏讀與口糊補字）**：
   - 臺灣華語自然語速約 **3.8～4.5 字／秒**。單鏡時長設為 `ceil(中文字數 / 4) + 1 秒`（範圍 4～15 秒，建議 $\le 12$ 秒），切勿多給 2 秒以上空檔逼迫模型補字或漏讀英文提示詞。
   - `<d>[Chinese] 核定繁中台詞</d>` 前方只寫極簡情緒與動作，禁止複雜英文抽象詞彙。
   - `overall_soundscape` 固定註明 `Clean dialogue strictly in Taiwanese-accented Mandarin Chinese only. Zero English words, no stuttering, no extra speech before or after the exact Chinese sentence.`。
7. **純底部卡拉 OK 逐字高亮繁中字幕（去上方突兀字卡）**：
   - **不壓制畫面上方突兀標題卡或浮動要件卡**，全片僅保留畫面底部安全區（9:16 `MarginV=240`）之純繁體中文對白字幕。
   - 採 Whisper 逐字時間戳 1:1 對齊核定台詞，輸出 ASS `\kf` 卡拉 OK 高亮效果：**未唸到純白（`#FFFFFF`）、唸到當下即時平滑標註為亮金色（`#FFD938`）**，並保留自然語氣停頓。

---

## 二、端到端標準工作流

### 階段 1：需求確認與劇本校正
1. 若使用者尚未提供完整條件，參考 `references/one-shot-prompt-template.md` 一次收齊必要規格（主題、比例、風格、角色與服裝、核定台詞、字幕與配音模式）。
2. 執行知識／法規查核與分鏡拆解（每鏡 4～15 秒、相鄰鏡頭交錯景別），呈現分鏡表待使用者核准。

### 階段 2：角色定妝與首幀準備
1. 依核准風格（如 3D 生活情境動畫或臺灣寫實人像）產出一致的角色與場景參考圖（直式 9:16 建議 576×1024 或等比構圖），存於專案 `references/`。
2. 為每個鏡頭指定對應的 `reference_images`（1～9 張），確保角色服裝與背景在跨鏡間一致。

### 階段 3：Colab A100 批次推論
1. 推論前先檢查 Colab 運算單位餘額：
   ```powershell
   python scripts/runner.py usage --json
   ```
2. 備妥 UTF-8 JSON 任務清單（`jobs.json`），使用直式筆記本 `assets/MiniMax_H3_Turbo_Portrait.ipynb`（或橫式 1376×768）於同一 Colab A100 工作階段批次執行，結束後自動停機不浪費額度：
   ```powershell
   python scripts/runner.py batch --manifest jobs.json --gpu A100 --no-high-mem --stop-on-complete --timeout 2400
   ```
3. 若遭遇暫時性 `503 Service Unavailable`，先確認無殘留工作階段（`colab sessions`）後重試一次；切勿留置閒置 GPU 跨對話計費。

### 階段 4：自動化品管驗收（ASR + 視覺抽幀）
詳見 `references/pitfalls-and-qa-checklist.md`，交付前必過四關：
1. **Whisper 逐字語音驗收**：執行 `scripts/review_speech.py` 檢查所有片段，確認：
   - **零英文漏讀**（不含 `[A-Za-z]` 異常英文詞）。
   - **無開頭／結尾口糊補字**，字數與核定台詞吻合。
2. **視覺抽幀驗收**：每鏡抽首、中、尾幀檢視：
   - 角色臉孔、眼鏡、服裝無跨鏡漂移或中途變身。
   - 畫面內無 AI 幻覺亂碼字牌或殘影。
   - 相鄰鏡頭視角有變化、無跳幀感。
3. **只重抽異常鏡頭**：保留已通過的片段，僅針對未過關鏡頭修正提示詞或時長後重製。

### 階段 5：卡拉 OK 字幕合成與最終交付
1. 將各幕通過驗收的語音起迄寫入 `dialogue-timing.json`。
2. 執行 `scripts/assemble_karaoke.py` 自動讀取 `speech-review/*.json` 逐字時間戳，產生純底部 ASS `\kf` 卡拉 OK 繁中字幕並透過 FFmpeg 壓制 1080×1920（H.264 CRF 19 + AAC 48kHz 160k）成片。
3. 以 `ffprobe`、`volumedetect` 及中段抽幀驗證卡拉 OK 白轉金高亮與音畫同步，最後更新專案 `handoff.md` 並交付成果路徑。

---

## 三、套件目錄結構

- `SKILL.md`：紅焰教學影音工作流主規範（本檔）
- `assets/MiniMax_H3_Turbo_Portrait.ipynb`：Colab MiniMax H3 直式 9:16（576×1024）推論筆記本
- `scripts/runner.py`：Colab CLI 工作階段與批次推論控制器
- `scripts/review_speech.py`：Faster-Whisper 逐字時間戳抽取與英文漏讀檢查腳本
- `scripts/assemble_karaoke.py`：FFmpeg 影音縫合與 ASS `\kf` 卡拉 OK 逐字高亮字幕壓制腳本
- `references/one-shot-prompt-template.md`：一次成型免修改提示詞範本
- `references/pitfalls-and-qa-checklist.md`：紅焰教學實戰踩坑與驗收清單
