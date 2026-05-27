"""
文档加载模块
支持 .txt / .md / .docx / .pdf 四种格式
统一返回 [{"source": 文件名, "content": 纯文本}]
"""

from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf"}


def load_documents(data_dir: Path) -> list[dict]:
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
    return path.read_text(encoding="utf-8")


def _parse_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())


def _parse_pdf(path: Path) -> str:
    import fitz

    doc = fitz.open(str(path))
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n\n".join(pages)
