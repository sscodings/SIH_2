import os
import sys
import re
from typing import List, Tuple
from pypdf import PdfReader, PdfWriter

def norm(text: str) -> str:
    """Normalize text by stripping all whitespace and lowercasing for robust fuzzy matching."""
    return re.sub(r"\s+", "", (text or "")).lower()

def find_schedule_pages(reader: PdfReader) -> List[int]:
    """Finds 0-indexed page numbers containing BSA Section 63 Schedule (Parts A and B)."""
    hits = []
    for i, p in enumerate(reader.pages):
        n = norm(p.extract_text())
        if (
            "tobefilledbytheparty" in n
            or "tobefilledbytheexpert" in n
            or "seesection63(4)(c)" in n
            or ("theschedule" in n and "section63" in n)
        ):
            hits.append(i)
    return hits

def extract_schedule_from_pdf(src_path: str, output_path: str) -> List[int]:
    """Extracts schedule pages from a given PDF source and writes to output_path."""
    if not os.path.exists(src_path):
        print(f"Error: Source file '{src_path}' not found.")
        return []

    reader = PdfReader(src_path)
    total_pages = len(reader.pages)
    print(f"Scanning '{os.path.basename(src_path)}' ({total_pages} pages)...")

    hits = find_schedule_pages(reader)
    print(f"Matching schedule pages found (0-based): {hits}")

    if hits:
        writer = PdfWriter()
        for i in hits:
            writer.add_page(reader.pages[i])
        
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
        print(f"Successfully extracted {len(hits)} page(s) -> '{output_path}'")
    else:
        print("No matching schedule pages found in this PDF.")

    return hits

def scan_all_research_pdfs(research_dir: str, output_filename: str = "bsa63_schedule_form.pdf"):
    """Scans all PDF files in the research directory and extracts schedule forms."""
    print(f"Scanning all PDFs in '{research_dir}'...\n" + "=" * 50)
    pdf_files = [f for f in os.listdir(research_dir) if f.lower().endswith(".pdf")]
    
    found_any = False
    for fname in sorted(pdf_files):
        # Skip previously extracted forms to avoid recursive extraction
        if "schedule_form" in fname.lower():
            continue
        fpath = os.path.join(research_dir, fname)
        out_path = os.path.join(research_dir, f"{os.path.splitext(fname)[0]}_schedule_extracted.pdf")
        hits = extract_schedule_from_pdf(fpath, out_path)
        if hits:
            found_any = True
            # Also update canonical bsa63_schedule_form.pdf from the official English gazette
            if "250882_english" in fname.lower():
                canonical_out = os.path.join(research_dir, output_filename)
                extract_schedule_from_pdf(fpath, canonical_out)
        print("-" * 50)

    if not found_any:
        print("No schedule pages matched across research directory.")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    default_research_dir = os.path.join(current_dir, "research")

    if len(sys.argv) > 1 and sys.argv[1] not in ("--all", "-a"):
        src = sys.argv[1]
        out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(default_research_dir, "bsa63_schedule_form.pdf")
        extract_schedule_from_pdf(src, out)
    else:
        scan_all_research_pdfs(default_research_dir)
