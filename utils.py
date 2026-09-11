def reconstruct_abstract_from_aii(aii):
    if not aii or not isinstance(aii, dict):
        return "摘要格式不符。"

    max_pos = -1

    for word_positions in aii.values():
        if word_positions:
            for pos in word_positions:
                if pos > max_pos:
                    max_pos = pos

    if max_pos == -1:
        has_zero_pos = any(0 in positions for positions in aii.values() if positions)
        if has_zero_pos and max_pos == -1:
            max_pos = 0

    abstract_list = [""] * (max_pos + 1)

    for word, positions in aii.items():
        if positions:
            for pos in positions:
                if 0 <= pos < len(abstract_list):
                    abstract_list[pos] = word

    reconstructed = " ".join(w for w in abstract_list if w)

    return reconstructed if reconstructed else "摘要是空的。"

def generate_papers_html(papers):
    if not isinstance(papers, list):
        return "<p>錯誤：資料格式錯誤，無法生成表格。</p>"

    html = "<table border='1' style='border-collapse: collapse; width: 100%; table-layout: fixed;'>"
    html += "<tr><th style='width: 5%;'>序號</th><th style='width: 30%;'>標題</th><th style='width: 10%;'>年份</th><th style='width: 10%;'>引用數</th><th style='width: 45%;'>中文摘要</th></tr>"

    for idx, paper in enumerate(papers, 1):
        try:
            title = paper.get('title', 'N/A')
            year = paper.get('publication_year', 'N/A')
            citations = paper.get('cited_by_count', 'N/A')
            abstract = paper.get("llm_generated_chinese_summary", "N/A").replace("\n", "<br>")
        except Exception as e:
            return f"<p>生成表格過程中出現錯誤：{e}</p>"

        html += f"""
            <tr>
                <td>{idx}</td>
                <td>{title}</td>
                <td>{year}</td>
                <td>{citations}</td>
                <td style='white-space: pre-wrap; word-wrap: break-word;'>{abstract}</td>
            </tr>
        """

    html += "</table>"

    return html