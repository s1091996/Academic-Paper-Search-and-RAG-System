import os
import requests
import pymupdf
import faiss
from sentence_transformers import SentenceTransformer
from groq import Groq
import gradio as gr

import paper_search
from config import EMBEDDING_MODEL, ARXIV_PDF_DIR, CHUNK_SIZE, CHUNK_OVERLAP, RAG_TOP_K, GROQ_MODEL
from llm import get_groq_api_key

index = None
embedder = None
all_chunks = None

def download_pdf_from_arxiv(arxiv_id, save_dir=ARXIV_PDF_DIR):
    os.makedirs(save_dir, exist_ok=True)
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    pdf_path = os.path.join(save_dir, f"{arxiv_id}.pdf")

    if not os.path.exists(pdf_path):
        try:
            resp = requests.get(pdf_url)
            if resp.status_code == 200:
                with open(pdf_path, "wb") as f:
                    f.write(resp.content)
                print(f"已下載 arXiv 論文: {pdf_path}")
            else:
                print(f"無法下載 arXiv 論文: {arxiv_id}")
                return None
        except Exception as e:
            print(f"下載 PDF 錯誤: {e}")
            return None

    return pdf_path

def extract_text_from_pdf(pdf_path):
    try:
        doc = pymupdf.open(pdf_path)
        texts = [page.get_text() for page in doc]
        return "\n".join(texts)
    except Exception as e:
        print(f"提取 PDF 內容錯誤: {e}")
        return ""

def split_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    i = 0

    while i < len(text):
        chunks.append(text[i:i+chunk_size])
        i += chunk_size - overlap

    return chunks

def build_faiss_index(chunks, embedder):
    embeddings = embedder.encode(
        chunks,
        convert_to_numpy=True,
        show_progress_bar=True
    )

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings.astype('float32'))

    return index

def get_prompt_from_chunks(index, chunks, question, embedder, top_k=RAG_TOP_K):
    q_vec = embedder.encode(
        [question],
        convert_to_numpy=True
    )

    _, I = index.search(
        q_vec.astype('float32'),
        top_k
    )

    retrieved = "\n".join([chunks[i] for i in I[0]])

    prompt = f"根據以下內容，以台灣人習慣的繁體中文回答問題。\n\n{retrieved}\n\n問題：{question}"

    return prompt

def build_index_from_selected_papers(papers):
    all_chunks = []
    paper_info = {}

    try:
        embedder = SentenceTransformer(EMBEDDING_MODEL)
    except Exception as e:
        return None, None, [], f"初始化嵌入模型失敗: {e}"

    status_messages = []

    for i, paper in enumerate(papers):
        arxiv_id = paper.get("arxiv_id")

        if not arxiv_id:
            status_message = f"無 arXiv ID，跳過論文：{paper.get('title')}"
            status_messages.append(status_message)
            continue

        status_message = f"下載並處理論文 {i+1}/{len(papers)}: {paper.get('title')}"
        status_messages.append(status_message)

        pdf_path = download_pdf_from_arxiv(arxiv_id)

        if pdf_path:
            text = extract_text_from_pdf(pdf_path)

            if not text.strip():
                status_message = f"PDF 內容空白，跳過：{pdf_path}"
                status_messages.append(status_message)
                continue

            chunks = split_text(text)

            chunk_indices = list(
                range(
                    len(all_chunks),
                    len(all_chunks) + len(chunks)
                )
            )

            paper_info[arxiv_id] = {
                'title': paper.get('title'),
                'chunk_indices': chunk_indices
            }

            all_chunks.extend(chunks)

            status_message = f"成功處理論文：{paper.get('title')} (chunks: {len(chunks)})"
            status_messages.append(status_message)

    if not all_chunks:
        return None, None, [], "所有論文都沒有可用的 PDF 或內容為空，無法建立向量庫。"

    try:
        index = build_faiss_index(all_chunks, embedder)
        status_message = f"成功建立向量索引 (total chunks: {len(all_chunks)})"
        status_messages.append(status_message)

        return index, embedder, all_chunks, "\n".join(status_messages)

    except Exception as e:
        return None, None, [], f"建立向量索引失敗: {e}"

def build_rag_system(progress=gr.Progress()):
    global index, embedder, all_chunks

    if not paper_search.all_selected_papers:
        return "沒有選定的論文，無法建立 RAG 系統。"

    progress(0.1, "開始建立 RAG 系統...")

    index, embedder, all_chunks, status = build_index_from_selected_papers(
        paper_search.all_selected_papers
    )

    if index is None:
        return status

    progress(1.0, "RAG 系統建立完成！")

    return status

def ask_question(question):
    global index, embedder, all_chunks

    if index is None or embedder is None or not all_chunks:
        return "RAG 系統尚未建立，請先點擊「建立 RAG 系統」按鈕。"

    if not question.strip():
        return "請輸入問題。"

    api_key = get_groq_api_key()

    if not api_key:
        return "Groq API 金鑰未設定，無法回答問題。"

    try:
        client = Groq(api_key=api_key)
        llm_model = GROQ_MODEL
    except Exception as e:
        return f"初始化 Groq Client 失敗: {e}"

    try:
        prompt = get_prompt_from_chunks(
            index,
            all_chunks,
            question,
            embedder
        )

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=llm_model,
            temperature=0.5
        )

        answer = chat_completion.choices[0].message.content.strip()

        return f"=== 回答 ===\n{answer}"

    except Exception as e:
        return f"發生錯誤：{str(e)}"