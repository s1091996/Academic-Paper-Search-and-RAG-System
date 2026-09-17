# Academic Paper Search and RAG System

## 1. 專案簡介（Overview）

本專案是一個結合學術資料庫檢索、大型語言模型（LLM）與檢索增強生成（RAG）技術的論文搜尋與問答系統。

在進行學術研究時，研究人員通常需要花費大量時間在文獻資料庫中搜尋論文，並閱讀大量不相關的摘要，並在冗長的論文全文中尋找特定問題的答案。本專案透過串接 OpenAlex 與 arXiv 資料庫，利用 LLM 自動搜尋關鍵字、評估論文是否符合研究需求並生成中文摘要；同時整合 FAISS 向量資料庫，針對選定論文的全文建立索引，讓使用者能透過LLM直接與論文內容進行問答，有效提升文獻整理的效率。

## 2. 功能特色（Features）

- **關鍵字生成**：根據使用者輸入的研究問題、應用領域、已知關鍵字與偏好，由 Groq LLM 自動生成 3 至 5 組適合學術資料庫搜尋的關鍵字詞組。
- **條件搜索**：透過 OpenAlex API 搜尋學術論文，可以指定發表年份範圍，並可輸入例如「高被引論文」或「綜述型論文（Review）」等等不同的搜尋條件。
- **LLM 相關性評估與中文摘要**：透過 LLM 依據研究條件對論文摘要進行檢查（SELECT / REJECT），為符合使用者需求的論文自動生成 100～250 字的繁體中文摘要。
- **arXiv 論文關聯與 PDF 下載**：比對被選中論文的標題，自動查詢 arXiv API 獲取對應的 arXiv ID，並將 PDF 全文下載儲存於本地。
- **全文向量化與 RAG 智慧問答**：使用 PyMuPDF 提取 PDF 內容並切分成文字區塊，利用 SentenceTransformer 與 FAISS 建立向量索引；提問時檢索關聯度最高的內文片段，由 LLM 統整出清晰的繁體中文解答。
- **雙分頁互動介面**：使用 Gradio 建立簡潔直覺的 Web 介面，依序提供「1. 論文搜尋」與「2. 論文問答」兩個操作頁面。

## 3. 系統流程／架構（System Architecture）

```text
使用者輸入研究需求
        ↓
LLM 生成多組搜尋關鍵字
        ↓
OpenAlex 檢索論文資料
        ↓
LLM 評估論文相關性並生成中文摘要
        ↓
查詢 arXiv API 並下載論文 PDF 全文
        ↓
PDF 文字提取、切塊與 FAISS 向量索引建立
        ↓
使用者提問 → 檢索最相關片段 → LLM 生成繁體中文回答
```

## 4. 專案結構（Project Structure）

```text
Academic-Paper-Search-and-RAG-System/
├── .env
├── .gitignore
├── README.md
├── app.py
├── config.py
├── llm.py
├── paper_search.py
├── rag.py
└── utils.py
```

| 檔案 | 用途 |
| --- | --- |
| app.py | 系統主程式；使用 Gradio 建立網頁介面，提供論文搜尋與問答兩個介面。 |
| paper_search.py | 論文搜尋邏輯；串接 OpenAlex 與 arXiv API，並使用 LLM 評估論文與生成摘要。 |
| rag.py | RAG 檢索增強系統；負責 PDF 下載、文字萃取、文字切塊、FAISS 向量索引建立與問答生成。 |
| llm.py | 封裝 Groq API 呼叫；負責產生搜尋關鍵字以及評估論文是否符合需求並輸出 JSON 格式摘要。 |
| config.py | 專案全域設定；定義 LLM 模型名稱、OpenAlex 使用者 Email、文字切塊大小與搜尋論文數量等參數。 |
| utils.py | 輔助工具函式|
| .env | 環境變數設定檔；存放 Groq API 金鑰（需自行建立）。 |
| .gitignore | Git 忽略規則；排除虛擬環境、暫存檔、.env 與下載的 PDF 資料夾。 |
| README.md | 專案說明文件。 |

## 5. 安裝與快速開始（Installation & Quick Start）

### 必要環境

- Python 3.8 或以上版本
- 具備有效之 Groq API 金鑰

### 安裝步驟

#### Windows (PowerShell)

`powershell
# 1. 複製專案
git clone https://github.com/s1091996/Academic-Paper-Search-and-RAG-System.git

# 2. 進入專案目錄
cd Academic-Paper-Search-and-RAG-System

# 3. 建立虛擬環境
python -m venv venv

# 4. 啟動虛擬環境
venv\Scripts\activate

# 5. 安裝必要套件
pip install gradio pyalex groq pymupdf faiss-cpu sentence-transformers python-dotenv requests

# 6. 設定環境變數
# 請在專案根目錄新增 .env 檔案，並填入您的 Groq API 金鑰：
# GROQ_API_KEY=your_groq_api_key_here

# 7. 啟動程式
python app.py
`
## 6. 使用範例（Usage / Examples）

啟動程式後，終端機會顯示本地伺服器網址（預設為 http://127.0.0.1:7860），請使用瀏覽器開啟該網址。

### 階段一：論文搜尋

1. 切換至 **1. 論文搜尋** 分頁。
2. 填寫研究需求資訊：
   - **研究問題/主題**：例如 LLM 在推薦系統中的應用
   - **應用領域 (可選)**：例如 電子商務
   - **已知關鍵字 (用逗號分隔)**：例如 LLM, recommendation, semantic
   - **年份範圍**：例如 2020-2025
   - **其他偏好**：例如 高度被引用、綜述型論文
3. 點擊 **「搜尋論文」** 按鈕。
4. 系統將依序執行以下處理：
   - 呼叫 Groq LLM 生成 3～5 組搜尋關鍵字詞組。
   - 透過 OpenAlex API 檢索符合年份與偏好的論文。
   - 還原論文摘要並由 LLM 逐篇評估是否採納（SELECT / REJECT）。
   - 對採納的論文自動生成繁體中文摘要，並查詢 arXiv API 補充 arXiv ID。
5. 檢視結果：
   - 右側 **「搜尋進度與結果」** 欄位會即時顯示搜尋與評估歷程。
   - 下方 **「選中的論文」** 區塊會以表格列出通過篩選的論文標題、年份、引用數及繁體中文摘要。

### 階段二：論文問答

1. 完成搜尋並確認有選中的論文後，切換至 **2. 論文問答** 分頁。
2. 點擊 **「建立 RAG 系統」** 按鈕：
   - 系統將依據選中論文的 arXiv ID，自動下載 PDF 全文至 pdfs/ 資料夾。
   - 提取 PDF 文字、依照設定進行文字切塊，並使用 SentenceTransformer 與 FAISS 建立向量檢索索引。
   - 建立完成後，「RAG 系統狀態」欄位將顯示索引建立成功訊息與總切塊數量。
3. 在 **「輸入問題」** 欄位輸入您想詢問的學術問題：
   - 例如：這些論文提出了哪些主要的 LLM 應用方式？
4. 點擊 **「提問」** 按鈕：
   - 系統會從向量索引庫檢索出最相關的論文段落，送交 Groq LLM 生成繁體中文統整回答，並顯示於 **「回答」** 區塊。

## 7. 限制與注意事項（Limitations / Notes）

- **需要 Groq API 金鑰**：本系統依賴 Groq API 進行關鍵字生成、論文審查與問答生成，使用前請務必在 .env 中設定有效的 GROQ_API_KEY，並注意 API 的使用額度與頻率限制。
- **arXiv PDF 下載限制**：全文問答（RAG）功能依賴 arXiv 公開論文；若搜尋到的論文未收錄於 arXiv 或無法透過標題查詢到對應的 arXiv ID，則無法下載 PDF 納入向量索引。
- **初次執行需下載模型**：系統預設使用 ll-MiniLM-L6-v2 嵌入模型，首次執行建立 RAG 系統時需自網路下載模型權重檔，需要穩定的網路連線並佔用部分記憶體。
- **操作順序相依性**：系統採用全域狀態記錄選中論文，必須先在「1. 論文搜尋」分頁成功取得論文後，才能在「2. 論文問答」分頁建立 RAG 系統與提問。
- **OpenAlex 聯絡資訊**：建議在 config.py 中將 OPENALEX_EMAIL 更新為您個人的 Email，以符合 OpenAlex 的請求原則（Polite Pool），確保連線穩定。
