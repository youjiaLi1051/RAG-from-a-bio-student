"""
文档加载模块
支持 .txt / .md / .docx / .pdf 四种格式
统一返回 [{"source": 文件名, "content": 纯文本}]
"""

from pathlib import Path

from src.config import DATA_DIR

SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf"}


def load_documents(data_dir: Path = DATA_DIR) -> list[dict]:
    """扫描 data_dir，加载所有支持格式的文档"""
    documents = []
    for file_path in sorted(data_dir.iterdir()):
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        text = _parse_file(file_path)
        if not text.strip():
            continue
        documents.append({"source": file_path.name, "content": text})
        print(f"  已加载: {file_path.name} ({len(text)} 字符)")
    return documents


def _parse_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".txt", ".md"):
        return _parse_text(path)
    if ext == ".docx":
        return _parse_docx(path)
    if ext == ".pdf":
        return _parse_pdf(path)
    raise ValueError(f"不支持的文件格式: {ext}")


def _parse_text(path: Path) -> str:
    text = _read_auto_encoding(path)
    if path.suffix.lower() == ".md":
        text = _markdown_to_text(text)
    return text


def _read_auto_encoding(path: Path) -> str:
    """自动检测编码读取文本文件"""
    raw = path.read_bytes()
    # 尝试常见编码
    for encoding in ["utf-8", "gbk", "gb2312", "gb18030", "latin-1"]:
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    # 兜底：忽略无法解码的字节
    return raw.decode("utf-8", errors="ignore")


def _markdown_to_text(md: str) -> str:
    """将 markdown 转为纯文本，去掉标记但保留内容结构"""
    import markdown
    from bs4 import BeautifulSoup

    html = markdown.markdown(md, extensions=["tables", "fenced_code"])
    soup = BeautifulSoup(html, "html.parser")

    # 在块级元素前后加换行，保留段落结构
    for tag in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "br"]):
        tag.insert_before("\n")
        tag.insert_after("\n")

    text = soup.get_text()

    # 清理多余空行
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")

    return text.strip()


def _parse_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    parts = []

    # 遍历文档主体，按顺序提取段落和表格
    for element in doc.element.body:
        tag = element.tag.split("}")[-1]  # 去掉命名空间

        if tag == "p":
            # 段落
            text = element.text or ""
            # 段落内可能有多个 run
            for run in element.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
                if run.text:
                    text += run.text
            if text.strip():
                parts.append(text.strip())

        elif tag == "tbl":
            # 表格：转为文本格式
            table_text = _docx_table_to_text(element)
            if table_text:
                parts.append(table_text)

    return "\n\n".join(parts)


def _docx_table_to_text(table_element) -> str:
    """将 docx 表格 XML 转为文本"""
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    rows = []
    for tr in table_element.findall(f".//{ns}tr"):
        cells = []
        for tc in tr.findall(f".//{ns}tc"):
            cell_text = ""
            for t in tc.findall(f".//{ns}t"):
                if t.text:
                    cell_text += t.text
            cells.append(cell_text.strip())
        if any(cells):
            rows.append(cells)

    if not rows:
        return ""

    # 转为对齐的文本表格
    col_widths = [max(len(row[i]) if i < len(row) else 0 for row in rows) for i in range(max(len(r) for r in rows))]
    lines = []
    for row in rows:
        cells = [row[i].ljust(col_widths[i]) if i < len(row) else " " * col_widths[i] for i in range(len(col_widths))]
        lines.append(" | ".join(cells))
    return "\n".join(lines)


def _parse_pdf(path: Path) -> str:
    import fitz

    doc = fitz.open(str(path))
    parts = []

    for page_num, page in enumerate(doc):
        # 提取文本
        text = page.get_text()
        if text.strip():
            parts.append(text.strip())

        # 尝试提取表格
        try:
            tables = page.find_tables()
            for table in tables:
                table_data = table.extract()
                if table_data:
                    # 转为文本格式
                    col_widths = [max(len(str(row[i])) if i < len(row) else 0 for row in table_data)
                                  for i in range(max(len(r) for r in table_data))]
                    lines = []
                    for row in table_data:
                        cells = [str(row[i]).ljust(col_widths[i]) if i < len(row) else " " * col_widths[i]
                                 for i in range(len(col_widths))]
                        lines.append(" | ".join(cells))
                    parts.append("\n".join(lines))
        except Exception:
            pass  # 某些 PDF 不支持表格提取，忽略

    doc.close()
    return "\n\n".join(parts)
