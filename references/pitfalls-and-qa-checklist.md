# 紅焰教學｜MiniMax H3 實戰踩坑與驗收清單

本文件彙整自「紅焰教學」9:16 法律科普短片實際製作過程中遇到的所有真實缺陷與根治對策，供每次開案與驗收逐項查核。

---

## 一、五大真實踩坑與根治法則

| 編號 | 實戰遇到的缺陷現象 | 真正成因 | 根治做法（已內建於本技能） |
| :--- | :--- | :--- | :--- |
| **1** | **雙人鏡頭中途變臉換裝**（藍衣主管講到一半突變成戴眼鏡西裝律師） | `subject_definitions` 順手把整部片所有角色（含未出場的律師）都寫進了該鏡 prompt。 | 每鏡 `subject_definitions` **嚴格只寫該幕出場角色**；雙人鏡頭寫明 `LEFT`/`RIGHT`、`no glasses` 與 `Continuous uncut take, maintain both original faces and original clothes`。 |
| **2** | **單人鏡頭服裝串場**（律師解說時誤穿成苦主的米色毛衣） | `subject_definitions` 開頭先描述苦主服裝，模型將前段服裝權重套在律師臉上。 | 單人鏡頭只寫該單一角色之服裝與特徵，完全不提其他角色服裝。 |
| **3** | **畫面下半部冒出 AI 亂碼字牌**（「最捩發椡...」） | Prompt 寫了 `leave the lower half available for an editorial information card`，模型誤以為要畫出實體字牌。 | Prompt 全面禁用 `card`、`board`、`sign`、`title`、`overlay` 等誘導字；寫死 `Absolutely no generated text, signs, boards, placards, cards, subtitles or overlays`。 |
| **4** | **旁白誤讀英文提示詞或開頭口糊補字**（唸出 `channels` 或開頭含糊補字） | 1. 單鏡秒數給太長（如 31 字給 10 秒、18 字給 6 秒），模型為填滿時間而漏讀 prompt 英文或胡亂補字。<br>2. 對白前寫了複雜英文描述。 | 1. 秒數採 `ceil(字數 / 4) + 1 秒` 精準配比。<br>2. `<d>[Chinese] ... </d>` 前僅保留極簡語氣描述。<br>3. `overall_soundscape` 寫明 `Strictly Mandarin Chinese only, zero English words`。 |
| **5** | **相鄰兩鏡硬切出現跳幀感**（1:14 切 1:15 畫面微跳不自然） | 第 7 幕與第 8 幕皆使用同一張律師近景參考圖直接硬切。 | **相鄰鏡頭必須切換景別與構圖**（例如：單人近景 $\rightarrow$ 雙人溫馨收尾中景）。 |

---

## 二、交付前必檢驗收清單（QA Checklist）

### A. 語音與台詞驗收（`scripts/review_speech.py`）
- [ ] 全數鏡頭皆已執行 Whisper 逐字辨識並輸出 `speech-review/*.json`。
- [ ] **零英文漏讀**：辨識結果無任何不應出現的 `[A-Za-z]` 英文字母。
- [ ] **字數吻合**：辨識字數與核定繁中台詞一致，無開頭／結尾口糊補字。
- [ ] **臺灣口音與語氣**：確認語調自然、無過長死寂空檔。

### B. 畫面與角色驗收（抽幀檢查）
- [ ] 每鏡皆抽檢開頭、中段、結尾幀，角色臉孔、眼鏡、服裝 100% 一致。
- [ ] 全片無 AI 幻覺亂碼文字、字牌或背景怪字。
- [ ] 相鄰鏡頭景別交錯（中景／近景／雙人景），剪輯銜接無跳幀感。

### C. 字幕與成片技術驗收（`scripts/assemble_karaoke.py`）
- [ ] 全片 **100% 臺灣標準繁體中文**，無簡體字。
- [ ] **純底部字幕**：無畫面上方突兀標題卡或浮動字卡。
- [ ] **卡拉 OK 逐字高亮**：抽檢中段影格，確認未唸到為純白色、唸到當下已平滑標註為亮金色（`#FFD938`）。
- [ ] `ffprobe` 檢核：1080 × 1920（9:16）、24 fps、H.264 + AAC 48kHz。
- [ ] `volumedetect` 檢核：音量清晰（約 -16 至 -12 dB）、峰值 < 0 dB 無爆音。
- [ ] Colab GPU 確認已停止（`colab sessions` 無活動工作階段）。
