import gradio as gr
from paper_search import search_papers
from rag import build_rag_system, ask_question

all_selected_papers = []
index = None
embedder = None
all_chunks = None

with gr.Blocks(title="學術論文搜尋與問答系統") as app:
    gr.Markdown("# 學術論文搜尋與問答系統")

    with gr.Tab("1. 論文搜尋"):
        gr.Markdown("## 第一步：輸入研究需求")

        with gr.Row():
            with gr.Column():
                research_question = gr.Textbox(label="研究問題/主題", placeholder="例如：LLM 在推薦系統中的應用", lines=2)
                application_domain = gr.Textbox(label="應用領域 (可選)", placeholder="例如：電子商務", lines=1)
                known_keywords = gr.Textbox(label="已知關鍵字 (用逗號分隔)", placeholder="例如：LLM, recommendation, semantic", lines=1)
                year_range = gr.Textbox(label="年份範圍", placeholder="例如：2020-2024, 2022, 2021-", value="2020-2025")
                preferences = gr.Textbox(label="其他偏好", placeholder="例如：高度被引用、綜述型論文", lines=1)
                search_button = gr.Button("搜尋論文", variant="primary")

            with gr.Column():
                search_output = gr.Textbox(label="搜尋進度與結果", lines=20)
                papers_table = gr.HTML(label="選中的論文")

        search_button.click(
            fn=search_papers,
            inputs=[research_question, application_domain, known_keywords, year_range, preferences],
            outputs=[search_output, papers_table]
        )

    with gr.Tab("2. 論文問答"):
        gr.Markdown("## 第二步：建立 RAG 系統並提問")

        with gr.Row():
            build_rag_button = gr.Button("建立 RAG 系統", variant="primary")
            rag_status = gr.Textbox(label="RAG 系統狀態", lines=10)

        build_rag_button.click(fn=build_rag_system, outputs=rag_status)

        with gr.Row():
            question_input = gr.Textbox(label="輸入問題", placeholder="例如：這些論文提出了哪些主要的 LLM 應用方式？", lines=2)
            ask_button = gr.Button("提問", variant="primary")

        answer_output = gr.Textbox(label="回答", lines=15)

        ask_button.click(fn=ask_question, inputs=question_input, outputs=answer_output)

    gr.Markdown("""
    ### 系統說明
    1. **論文搜尋**：輸入您的研究需求，系統會從 OpenAlex 資料庫搜尋相關論文，並使用 LLM 評估是否符合您的需求。
    2. **建立 RAG 系統**：點擊建立 RAG 按鈕後，系統會下載選中論文的 PDF，並建立向量索引系統。
    3. **論文問答**：輸入問題，系統會使用 RAG 技術從論文中檢索相關內容並生成回答。

    提示：建議先輸入明確的研究需求，找到相關論文後，再建立 RAG 系統進行問答。
    RAG 系統建立需要時間，請耐心等待。
    """)

if __name__ == "__main__":
    app.launch()