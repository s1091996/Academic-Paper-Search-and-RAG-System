import os
import json
from dotenv import load_dotenv
from config import GROQ_MODEL

load_dotenv()

def get_groq_api_key():
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        print("GROQ_API_KEY沒設定。")
    return groq_api_key

def get_multiple_search_queries_from_llm(search_info, client, model=GROQ_MODEL):
    prompt_parts = [
        "根據以下研究論文的搜尋標準，請生成 3 到 5 個適合在學術數據庫（如 OpenAlex）中獨立使用的搜尋關鍵字詞組。",
        "每個關鍵字詞組可以是單個詞或一個短語。請用「逗號」分隔每個獨立的關鍵字詞組。",
        "例如：large language models, transformer architecture, natural language understanding, model quantization",
        "僅輸出逗號分隔的關鍵字詞組，不要包含任何其他文字、解釋、編號或引號。",
        "\n--- 研究標準 ---",
        f"研究問題/主題: {search_info['research_question']}"
    ]

    if search_info.get('application_domain'):
        prompt_parts.append(f"應用領域: {search_info['application_domain']}")
    if search_info.get('known_keywords'):
        prompt_parts.append(f"已知關鍵字: {', '.join(search_info['known_keywords'])}")
    if search_info.get('preferences'):
        prompt_parts.append(f"偏好: {search_info['preferences']}")

    prompt_parts.append("\n--- 生成的逗號分隔關鍵字詞組 ---:")

    prompt = "\n".join(prompt_parts)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
            temperature=0.5,
        )
        generated_text = chat_completion.choices[0].message.content.strip()
        return generated_text
    except Exception as e:
        print(f"LLM API失敗 (搜尋查詢生成): {e}")
        return ""

def evaluate_and_generate_chinese_summary_llm(paper_info_for_llm, original_search_criteria, client, model=GROQ_MODEL):
    prompt = f"""
    你是一位專業的學術研究助理 AI。你的任務是：
    1. 仔細閱讀以下提供的「論文詳細資訊」(包含其英文摘要) 以及研究人員的「原始搜尋條件」。
    2. 判斷這篇論文是否「高度符合」研究人員的「原始搜尋條件」。
    3. 一定要符合研究人員提出的「其他偏好」，只要不符合就REJECT。
    4. 如果你判斷論文為「高度符合」(SELECT)，請根據其「英文摘要」，為研究人員撰寫一份簡潔、專業、準確反映核心內容的「繁體中文摘要」(約100-250字)。
    5. 你的回答必須是 JSON 格式。

    --- 原始搜尋條件 ---
    研究問題/主題: {original_search_criteria.get('research_question', 'N/A')}
    應用領域: {original_search_criteria.get('application_domain', 'N/A')}
    已知關鍵字: {', '.join(original_search_criteria.get('known_keywords', []))}
    偏好年份範圍: {original_search_criteria.get('year_range', 'N/A')}
    其他偏好: {original_search_criteria.get('preferences', 'N/A')}
    --- 結束原始搜尋條件 ---

    --- 論文詳細資訊 ---
    標題: {paper_info_for_llm.get('title', 'N/A')}
    英文摘要: {paper_info_for_llm.get('abstract', '摘要不可用')}
    引用次數: {paper_info_for_llm.get('citation_count', 'N/A')}
    發表年份: {paper_info_for_llm.get('publication_year', 'N/A')}
    --- 結束論文詳細資訊 ---

    請嚴格按照以下 JSON 格式和繁體中文提供您的回應：
    {{
      "decision": "SELECT" or "REJECT",
      "reason": "使用台灣習慣的繁體中文，你判斷論文是否符合需求的理由（1-2句話）。",
      "chinese_summary": "如果 decision 是 SELECT，則此處為你生成的中文摘要；如果是 REJECT，則此處應為空字串或 \"N/A\"。"
    }}

    JSON 回應:
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        response_content = chat_completion.choices[0].message.content.strip()
        return response_content
    except Exception as e:
        return json.dumps({
            "decision": "REJECT",
            "reason": f"LLM API 呼叫失敗: {str(e)}",
            "chinese_summary": "N/A"
        })