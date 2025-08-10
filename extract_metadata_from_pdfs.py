"""
extract_metadata_from_pdfs.py

Place your dashboard PDF exports in ./pdfs/
Run: python extract_metadata_from_pdfs.py
Outputs: ./embeddings/dashboards_extracted.json
"""

import os
import re
import json
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io

# If Tesseract binary is not in PATH, set this to the tesseract executable, e.g.:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

PDF_DIR = "pdfs"
OUT_DIR = "pdf_extracted"
OUT_FILE = os.path.join(OUT_DIR, "dashboards_extracted.json")

# Regex patterns to capture "KPI name: value" or "KPI name value%" etc.
KPI_PATTERNS = [
    re.compile(r"(?P<name>[A-Za-z0-9 &/._\-]{3,100})[:\s\-]{1,4}(?P<value>\d{1,3}(?:[\.,]\d+)?\s?%)"),
    re.compile(r"(?P<name>[A-Za-z0-9 &/._\-]{3,100})[:\s\-]{1,4}([$€£]?\d{1,3}(?:[,\d]{0,3})*(?:\.\d+)?)"),
    re.compile(r"(?P<name>(?:[A-Za-z ]{2,50}?(?:rate|ratio|score|count|value|variance|growth|mean|avg|average|turnover|conversion|revenue|sales|churn|retention)))\s+[:\-\–]?\s*(?P<value>\d{1,3}(?:[\.,]\d+)?\s?%?)", re.I),
]

# Heuristic keywords to find KPI names in text
KPI_KEYWORDS = ["rate", "ratio", "score", "count", "value", "variance", "growth", "average", "mean", "turnover", "conversion", "revenue", "sales", "churn", "retention", "uptime", "mttr", "nps", "csat"]

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)  # ensure pdfs folder exists

def extract_text_blocks_from_pdf(path, max_pages=None):
    """
    Returns list of text blocks with fields: text, max_size, page_number
    """
    doc = fitz.open(path)
    blocks = []
    for page_idx, page in enumerate(doc):
        if max_pages and page_idx >= max_pages:
            break
        # get dictionary with text blocks and spans (font size available in spans)
        page_dict = page.get_text("dict", flags=0, sort=True)
        for b in page_dict.get("blocks", []):
            if b.get("type", 1) != 0:
                continue  # skip images/other non-text blocks
            block_text = []
            max_size = 0.0
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    txt = span.get("text", "")
                    size = span.get("size", 0)
                    block_text.append(txt)
                    if size and size > max_size:
                        max_size = size
            joined = " ".join([t.strip() for t in block_text if t.strip()])
            if joined:
                blocks.append({"text": joined, "max_size": max_size, "page": page_idx})
    doc.close()
    return blocks

def ocr_page_image(page, dpi=200):
    """
    Render a PyMuPDF page to an image and run pytesseract on it.
    Returns the OCR text for the page.
    """
    pix = page.get_pixmap(dpi=dpi, alpha=False)  # render to RGB
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    # Use pytesseract to extract text
    ocr_text = pytesseract.image_to_string(img)
    return ocr_text

def ocr_pdf(path, dpi=200, max_pages=None):
    """
    OCR entire PDF (used if text extraction fails)
    """
    doc = fitz.open(path)
    texts = []
    for i, page in enumerate(doc):
        if max_pages and i >= max_pages:
            break
        texts.append(ocr_page_image(page, dpi=dpi))
    doc.close()
    return "\n".join(texts)

def choose_title_and_description(blocks):
    """
    Choose title as the largest-font text block on first page (if present),
    else largest on whole document. Description: first few meaningful blocks combined.
    """
    if not blocks:
        return "", ""
    # prefer first page blocks for title
    first_page_blocks = [b for b in blocks if b["page"] == 0]
    candidate_blocks = first_page_blocks or blocks
    candidate_blocks_sorted = sorted(candidate_blocks, key=lambda b: b["max_size"] or 0, reverse=True)
    title = candidate_blocks_sorted[0]["text"].strip()
    # build description from first several blocks on first page (excluding title)
    desc_parts = []
    seen = set()
    for b in blocks:
        if b["text"].strip() and b["text"].strip() != title and len(desc_parts) < 4:
            txt = b["text"].strip()
            if txt not in seen:
                desc_parts.append(txt)
                seen.add(txt)
    description = " ".join(desc_parts).strip()
    return title, description

def extract_kpis_from_text(text):
    """
    Finds KPI candidates via regex and heuristics. Returns list of dicts {name, description}
    """
    kpis = []
    found_names = set()

    # 1) pattern-based captures
    for pat in KPI_PATTERNS:
        for m in pat.finditer(text):
            name = m.groupdict().get("name", "").strip(" :\n\t")
            value = m.groupdict().get("value", "").strip()
            if not name:
                continue
            name_clean = re.sub(r"\s{2,}", " ", name)
            if name_clean.lower() in found_names:
                continue
            found_names.add(name_clean.lower())
            desc = f"Detected value: {value}" if value else ""
            kpis.append({"name": name_clean, "description": desc})

    # 2) heuristic lines: lines containing '%' or currency or KPI keywords
    for line in text.splitlines():
        line_stripped = line.strip()
        if len(line_stripped) < 5:
            continue
        low = line_stripped.lower()
        if "%" in line_stripped or re.search(r"\$\s?\d", line_stripped) or any(k in low for k in KPI_KEYWORDS):
            # try to split "Name: value" or "Name - value"
            parts = re.split(r"[:\-–]{1,2}", line_stripped, maxsplit=1)
            if len(parts) == 2:
                cand_name = parts[0].strip()
                cand_value = parts[1].strip()
                if len(cand_name) > 2 and cand_name.lower() not in found_names:
                    found_names.add(cand_name.lower())
                    kpis.append({"name": cand_name, "description": f"Detected value: {cand_value}"})
            else:
                # treat whole line as candidate KPI label if it contains keywords
                candidate_words = re.sub(r"\s{2,}", " ", line_stripped)
                if len(candidate_words) > 10 and candidate_words.lower() not in found_names:
                    found_names.add(candidate_words.lower())
                    kpis.append({"name": candidate_words, "description": ""})

    # dedupe by name preserving order
    seen = set()
    cleaned = []
    for k in kpis:
        n = k["name"].strip()
        ln = n.lower()
        if ln in seen:
            continue
        seen.add(ln)
        cleaned.append({"name": n, "description": k.get("description", "")})
    return cleaned

def process_pdf_file(path):
    """
    Process one PDF and return an extracted metadata dict
    """
    print(f"Processing {path} ...")
    blocks = extract_text_blocks_from_pdf(path, max_pages=10)  # limit pages for speed; adjust as needed
    full_text = " ".join([b["text"] for b in blocks])

    # If extracted text is tiny, fallback to OCR for entire PDF
    if len(full_text.strip()) < 50:
        print(" - low text extracted, using OCR fallback")
        full_text = ocr_pdf(path, dpi=200, max_pages=10)

    title, description = choose_title_and_description(blocks)
    if not title:
        # fallback to filename
        title = os.path.splitext(os.path.basename(path))[0]

    # merge blocks and OCR text for KPI extraction to maximize matches
    combined_text = full_text
    kpis = extract_kpis_from_text(combined_text)

    meta = {
        "id": os.path.splitext(os.path.basename(path))[0],
        "name": title,
        "description": description or (combined_text[:500] + "..."),
        "tags": [],   # optional, can be filled via NER/LLM
        "url": "",    # no URL for PDF offline; keep blank
        "kpis": kpis
    }
    return meta

def process_all_pdfs(pdf_dir=PDF_DIR):
    out = []
    pdfs = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
    if not pdfs:
        print(f"No pdf files found in {pdf_dir}. Place your exported dashboard PDFs there.")
        return out
    for p in pdfs:
        path = os.path.join(pdf_dir, p)
        try:
            meta = process_pdf_file(path)
            out.append(meta)
        except Exception as e:
            print(f"Error processing {p}: {e}")
    # save file
    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print(f"Wrote {len(out)} dashboard entries to {OUT_FILE}")
    return out

if __name__ == "__main__":
    process_all_pdfs()
