import re
import json
import requests
import xml.etree.ElementTree as ET
import pyalex
from pyalex import Works
from groq import Groq
import gradio as gr

from config import GROQ_MODEL, OPENALEX_EMAIL, MAX_RESULTS_PER_QUERY
from llm import get_groq_api_key, get_multiple_search_queries_from_llm, evaluate_and_generate_chinese_summary_llm
from utils import reconstruct_abstract_from_aii, generate_papers_html

all_selected_papers = []

def search_openalex_papers(keywords_str, year_range_str, preferences_str, max_results_per_query=MAX_RESULTS_PER_QUERY):
    if not keywords_str:
        print("沒有可用的關鍵字進行搜尋。")
        return []

    pyalex.config.email = OPENALEX_EMAIL

    start_year, end_year = None, None
    year_filter_works = {}
    if year_range_str:
        year_range_str = year_range_str.strip()
        if re.match(r"^\d{4}$", year_range_str):
            start_year = int(year_range_str)
            year_filter_works = {'publication_year': f"{start_year}"}
        elif re.match(r"^\d{4}-\d{4}$", year_range_str):
            s, e = year_range_str.split('-')
            start_year, end_year = int(s), int(e)
            if start_year <= end_year:
                year_filter_works = {'publication_year': f"{start_year}-{end_year}"}
        elif re.match(r"^\d{4}-$", year_range_str):
            start_year = int(year_range_str[:-1])
            year_filter_works = {'from_publication_date': f"{start_year}-01-01"}
        elif re.match(r"^-\d{4}$", year_range_str):
            end_year = int(year_range_str[1:])
            year_filter_works = {'to_publication_date': f"{end_year}-12-31"}

    query_obj = Works().search(keywords_str)
    if year_filter_works:
        query_obj = query_obj.filter(**year_filter_works)

    sort_criteria = None
    if "高度被引用" in preferences_str or "高被引" in preferences_str:
        sort_criteria = {'cited_by_count': 'desc'}
    if "綜述型論文" in preferences_str or "review" in preferences_str.lower():
        query_obj = query_obj.filter(type='review')

    if sort_criteria:
        query_obj = query_obj.sort(**sort_criteria)

    found_papers_details = []
    try:
        retrieved_works = query_obj.get(per_page=max_results_per_query)
        count = 0
        for work in retrieved_works:
            if count >= max_results_per_query:
                break

            paper_details = {
                'title': work.get('title'),
                'doi': work.get('doi'),
                'publication_year': work.get('publication_year'),
                'authors': [authorship.get('author', {}).get('display_name') for authorship in work.get('authorships', []) if authorship.get('author', {}).get('display_name')],
                'primary_location_source_name': work.get('primary_location', {}).get('source', {}).get('display_name') if work.get('primary_location', {}).get('source') else "N/A",
                'cited_by_count': work.get('cited_by_count'),
                'openalex_id': work.get('id'),
                'abstract_inverted_index': work.get('abstract_inverted_index')
            }

            found_papers_details.append(paper_details)
            count += 1

    except Exception as e:
        print(f"OpenAlex 搜尋失敗: {e}")

    return found_papers_details

def evaluate_papers_for_query(query, user_search_info, client, llm_model, processed_ids, final_selected_list):
    status_msg = f"處理搜尋查詢: '{query}'"
    selection_results = []

    papers = search_openalex_papers(
        keywords_str=query,
        year_range_str=user_search_info['year_range'],
        preferences_str=user_search_info['preferences'],
        max_results_per_query=MAX_RESULTS_PER_QUERY
    )

    if not papers:
        status_msg += f"\n使用查詢 '{query}' 未從 OpenAlex 初步找到任何論文。"
        return status_msg, selection_results

    status_msg += f"\n找到 {len(papers)} 篇論文，開始評估..."

    for idx, paper in enumerate(papers):
        paper_id = paper.get('openalex_id')
        if paper_id in processed_ids:
            continue

        status_msg += f"\n--- 評估論文 {idx+1}/{len(papers)} ---"
        status_msg += f"\n標題: {paper.get('title', 'N/A')}"

        reconstructed_abstract = reconstruct_abstract_from_aii(paper.get('abstract_inverted_index', {}))

        paper_info = {
            'title': paper.get('title'),
            'abstract': reconstructed_abstract,
            'citation_count': paper.get('cited_by_count'),
            'publication_year': paper.get('publication_year')
        }

        llm_response = evaluate_and_generate_chinese_summary_llm(
            paper_info,
            user_search_info,
            client,
            llm_model
        )

        try:
            result = json.loads(llm_response)
            decision = result.get('decision', 'REJECT').upper()
            reason = result.get('reason', '無特定理由。')
            chinese_summary = result.get('chinese_summary', '')

            selection_results.append({
                'title': paper.get('title', 'N/A'),
                'decision': decision,
                'reason': reason
            })

            if decision == "SELECT" and chinese_summary.strip().lower() not in ['', 'n/a', '摘要不可用或格式不符。', '摘要內容為空或無法重建。']:
                status_msg += f"\nLLM 決定: {decision}"

                paper_copy = paper.copy()
                paper_copy['llm_selection_reason'] = reason
                paper_copy['original_reconstructed_abstract'] = reconstructed_abstract
                paper_copy['llm_generated_chinese_summary'] = chinese_summary
                paper_copy['arxiv_id'] = ""

                final_selected_list.append(paper_copy)

                status_msg += f"\n論文被選中並生成中文摘要，摘要預覽: {chinese_summary[:150]}..."
            else:
                if decision == "SELECT":
                    status_msg += f"\n論文被標記 SELECT，但中文摘要不符合要求，未採納。"
                else:
                    status_msg += f"\n論文未被選中，原因: {reason}"

        except json.JSONDecodeError:
            status_msg += f"\nLLM 回應非有效 JSON: {llm_response}"

            selection_results.append({
                'title': paper.get('title', 'N/A'),
                'decision': 'REJECT',
                'reason': 'LLM 回應格式錯誤，無法解析。'
            })

        except Exception as e:
            status_msg += f"\n解析 LLM 回應時錯誤: {e}"

            selection_results.append({
                'title': paper.get('title', 'N/A'),
                'decision': 'REJECT',
                'reason': f'處理時發生錯誤: {str(e)}'
            })

        if paper_id:
            processed_ids.add(paper_id)

    return status_msg, selection_results

def get_arxiv_id_by_title(title: str) -> str:
    if not title:
        return ""

    query = f"http://export.arxiv.org/api/query?search_query=all:{title}&sortBy=relevance&max_results=1"
    headers = {
        "User-Agent": "paper-recommender/1.0 (mailto:research@example.com)"
    }

    try:
        response = requests.get(query, headers=headers)

        if response.status_code != 200:
            return ""

        root = ET.fromstring(response.text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        entry = root.find('atom:entry', ns)

        if entry is not None:
            id_url = entry.find('atom:id', ns).text.strip()

            if "/abs/" in id_url:
                return id_url.split("/abs/")[-1]

    except Exception as e:
        print(f"查詢 arXiv ID 錯誤: {e}")

    return ""

def enrich_with_arxiv_ids(papers):
    for paper in papers:
        title = paper.get("title")
        arxiv_id = get_arxiv_id_by_title(title)
        paper["arxiv_id"] = arxiv_id

    return papers

def search_papers(research_question, application_domain, known_keywords, year_range, preferences, progress=gr.Progress()):
    global all_selected_papers

    all_selected_papers = []
    processed_paper_ids = set()
    all_selection_results = []

    api_key = get_groq_api_key()

    if not api_key:
        return "Groq API 金鑰未設定，無法繼續。", None

    try:
        client = Groq(api_key=api_key)
        llm_model = GROQ_MODEL
    except Exception as e:
        return f"初始化 Groq Client 失敗: {e}", None

    user_search_info = {
        'research_question': research_question,
        'application_domain': application_domain,
        'known_keywords': [k.strip() for k in known_keywords.split(',') if k.strip()],
        'year_range': year_range,
        'preferences': preferences
    }

    progress(0.1, "產生搜尋關鍵字中...")

    generated_queries = get_multiple_search_queries_from_llm(
        user_search_info,
        client,
        llm_model
    )

    if not generated_queries:
        return "未能從 LLM 產生有效搜尋查詢，無法繼續。", None

    queries = [q.strip() for q in generated_queries.split(',') if q.strip()]

    if not queries:
        return "LLM 未能生成有效的獨立搜尋查詢列表。", None

    query_progress = "生成的搜尋查詢列表: " + ", ".join(queries)

    full_progress = []
    full_progress.append(query_progress)

    for i, query in enumerate(queries):
        progress(
            (i + 1) / (len(queries) + 1),
            f"處理查詢 {i+1}/{len(queries)}: {query}"
        )

        status, selection_results = evaluate_papers_for_query(
            query,
            user_search_info,
            client,
            llm_model,
            processed_paper_ids,
            all_selected_papers
        )

        full_progress.append(status)
        all_selection_results.extend(selection_results)

    progress(0.95, "補充論文 arXiv ID...")

    all_selected_papers = enrich_with_arxiv_ids(all_selected_papers)

    results_summary = f"搜尋及評估完成。共選中 {len(all_selected_papers)} 篇論文。\n\n"
    results_summary += "=== 論文選擇結果 ===\n"

    for result in all_selection_results:
        results_summary += f"標題: {result['title']}\n"
        results_summary += f"決定: {result['decision']}\n"
        results_summary += f"原因: {result['reason']}\n"
        results_summary += "-" * 50 + "\n"

    progress(1.0, "搜尋完成！")

    return "\n".join(full_progress) + "\n" + results_summary, generate_papers_html(all_selected_papers)