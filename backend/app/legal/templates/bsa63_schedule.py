import os
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

OFFICIAL_BSA_PDF_SHA256 = "31ee68ea57b5303bf6697b5d8cb2004b9eb9180d7e9cbcbbdbf5bccab7cda5c1"
OFFICIAL_FORM_PDF_SHA256 = "c9b4f5032340d560d89f1ea27a9829d815a43a7b12e19a824481ef98d7ff65ed"
SCHEDULE_FOOTER = (
    "The Schedule [See section 63(4)(c)], Bharatiya Sakshya Adhiniyam, 2023 - "
    f"Gazette CG-DL-E-25122023-250882 | Official PDF SHA-256: {OFFICIAL_BSA_PDF_SHA256}"
)
LEGAL_PRE_DOWNLOAD_NOTICE = (
    "Part A and Part B are statements to be completed and signed by a person with knowledge "
    "and by an expert. This software does not sign or attest."
)

class NumberedCanvasWithWatermark(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        self.watermark_text = kwargs.pop("watermark_text", None)
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        self.saveState()
        # Draw watermark if court-readiness fails or draft
        if self.watermark_text:
            self.setFont("Helvetica-Bold", 46)
            self.setFillColor(colors.HexColor("#DC2626"), alpha=0.15)
            self.translate(300, 400)
            self.rotate(45)
            self.drawCentredString(0, 0, self.watermark_text)
            self.restoreState()
            self.saveState()

        # Running Footer
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(36, 20, SCHEDULE_FOOTER)
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(576, 20, page_str)
        self.restoreState()

def check_official_pdf_readiness() -> bool:
    """Verifies that the official Gazette PDF exists and matches the recorded hash."""
    candidates = [
        Path("docs/research/250882.pdf"),
        Path("backend/docs/research/250882.pdf")
    ]
    for p in candidates:
        if p.exists():
            h = hashlib.sha256(p.read_bytes()).hexdigest().lower()
            if h == OFFICIAL_BSA_PDF_SHA256:
                return True
    return False

def render_bsa63_certificate(
    output_path: Path,
    mode: str = "blank",  # "blank" | "prefilled"
    prefill_data: Optional[Dict[str, Any]] = None,
    hash_report_data: Optional[Dict[str, Any]] = None,
    is_court_ready: bool = True
) -> Path:
    """
    Renders the official BSA Section 63 Schedule certificate verbatim.
    Never alters, shortens, rewords or reorders any statutory phrase.
    """
    official_pdf_ok = check_official_pdf_readiness()
    court_ready = is_court_ready and official_pdf_ok

    watermark = None if court_ready else "NOT COURT-READY"
    if mode == "blank":
        watermark = None if official_pdf_ok else "NOT COURT-READY"

    prefill = prefill_data or {}
    report_data = hash_report_data or {}

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CertTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        alignment=1,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "CertSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        alignment=1,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        "CertBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        spaceAfter=6
    )
    bold_style = ParagraphStyle(
        "CertBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        spaceAfter=4
    )

    elements = []

    # ==================== PART A ====================
    elements.append(Paragraph("THE SCHEDULE", title_style))
    elements.append(Paragraph("[See section 63(4)(c)]", subtitle_style))
    elements.append(Paragraph("CERTIFICATE", subtitle_style))
    elements.append(Paragraph("PART A", subtitle_style))
    elements.append(Paragraph("(To be filled by the Party)", subtitle_style))
    elements.append(Spacer(1, 4))

    # Signatory line MUST be blank underscores
    elements.append(Paragraph(
        "I, _____________________ (Name), Son/daughter/spouse of ___________________ "
        "residing/employed at __________________________ do hereby solemnly affirm and "
        "sincerely state and submit as follows:",
        body_style
    ))
    elements.append(Paragraph(
        "I have produced electronic record/output of the digital record taken from the following "
        "device/digital record source (tick mark):",
        body_style
    ))

    # Device tick list
    src_tick = prefill.get("source_tick", "Server") if mode == "prefilled" else None
    tick_box = lambda name: f"[{'X' if src_tick == name else ' '}] {name}"
    device_table_data = [
        [tick_box("Computer / Storage Media"), tick_box("DVR"), tick_box("Mobile"), tick_box("Flash Drive")],
        [tick_box("CD/DVD"), tick_box("Server"), tick_box("Cloud"), tick_box("Other")]
    ]
    t_dev = Table(device_table_data, colWidths=[135, 135, 135, 135])
    t_dev.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(t_dev)
    elements.append(Spacer(1, 3))

    other_val = prefill.get("other_device", "") if mode == "prefilled" else ""
    other_str = f"<u>{other_val}</u>" if other_val else "________________________________________"
    elements.append(Paragraph(f"Other: {other_str}", body_style))

    make_model = prefill.get("make_model", "") if mode == "prefilled" else ""
    color = prefill.get("color", "") if mode == "prefilled" else ""
    serial = prefill.get("serial_number", "") if mode == "prefilled" else ""
    cloud_id = prefill.get("cloud_id", "") if mode == "prefilled" else ""
    other_info = prefill.get("other_relevant_info", "") if mode == "prefilled" else ""

    mm_str = f"<u>{make_model}</u>" if make_model else "_______________"
    col_str = f"<u>{color}</u>" if color else "_______________"
    ser_str = f"<u>{serial}</u>" if serial else "_______________"
    id_str = f"<u>{cloud_id}</u>" if cloud_id else "_____________________"
    oi_str = f"<u>{other_info}</u>" if other_info else "____"

    elements.append(Paragraph(f"Make & Model: {mm_str} Color: {col_str}", body_style))
    elements.append(Paragraph(f"Serial Number: {ser_str}", body_style))
    elements.append(Paragraph(f"IMEI/UIN/UID/MAC/Cloud ID{id_str} (as applicable)", body_style))
    elements.append(Paragraph(f"and any other relevant information, if any, about the device/digital record{oi_str}(specify).", body_style))

    # Control paragraph verbatim
    control_p = (
        "The digital device or the digital record source was under the lawful control for regularly "
        "creating, storing or processing information for the purposes of carrying out regular "
        "activities and during this period, the computer or the communication device was working "
        "properly and the relevant information was regularly fed into the computer during the "
        "ordinary course of business. If the computer/digital device at any point of time was not "
        "working properly or out of operation, then it has not affected the electronic/digital "
        "record or its accuracy. The digital device or the source of the digital record is:"
    )
    elements.append(Paragraph(control_p, body_style))

    # Owned / Maintained / Managed / Operated ticks exactly as printed
    elements.append(Paragraph("Owned &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Maintained &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Managed &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Operated", body_style))
    elements.append(Paragraph("by me (select as applicable).", body_style))


    # Hash paragraph
    manifest_hash = prefill.get("manifest_hash", "") if mode == "prefilled" else ""
    hash_str = f"<u>{manifest_hash}</u>" if manifest_hash else "_________________"
    elements.append(Paragraph(f"I state that the HASH value/s of the electronic/digital record/s is {hash_str},", body_style))
    elements.append(Paragraph("obtained through the following algorithm:", body_style))

    is_sha256 = (mode == "prefilled")
    algo_data = [
        [f"SHA1: [ ]"],
        [f"SHA256: [{'X' if is_sha256 else ' '}]"],
        [f"MD5: [ ]"],
        ["Other__________________ (Legally acceptable standard)"]
    ]
    t_algo = Table(algo_data, colWidths=[540])
    t_algo.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
    ]))
    elements.append(t_algo)
    elements.append(Paragraph("(Hash report to be enclosed with the certificate)", body_style))
    elements.append(Spacer(1, 4))

    # Part A Signatory block MUST remain blank
    elements.append(Paragraph("(Name and signature)", body_style))
    elements.append(Paragraph("Date (DD/MM/YYYY): _____", body_style))
    elements.append(Paragraph("Time (IST): ________hours (In 24 hours format)", body_style))
    elements.append(Paragraph("Place: ____________", body_style))

    # ==================== PAGE BREAK ====================
    elements.append(PageBreak())

    # ==================== PART B ====================
    elements.append(Paragraph("PART B", subtitle_style))
    elements.append(Paragraph("(To be filled by the Expert)", subtitle_style))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph(
        "I, ____________________ (Name), Son/daughter/spouse of _____________________ "
        "residing/employed at _________________________ do hereby solemnly affirm and "
        "sincerely state and submit as follows:",
        body_style
    ))
    elements.append(Paragraph(
        "The produced electronic record/output of the digital record are obtained from the following "
        "device/digital record source (tick mark):",
        body_style
    ))

    elements.append(t_dev)
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(f"Other: {other_str}", body_style))
    elements.append(Paragraph(f"Make & Model: {mm_str} Color: {col_str}", body_style))
    elements.append(Paragraph(f"Serial Number: {ser_str}", body_style))
    elements.append(Paragraph(f"IMEI/UIN/UID/MAC/Cloud ID{id_str} (as applicable)", body_style))
    elements.append(Paragraph(f"and any other relevant information, if any , about the device/digital record_______{oi_str}(specify).", body_style))

    elements.append(Paragraph(f"I state that the HASH value/s of the electronic/digital record/s is {hash_str},", body_style))
    elements.append(Paragraph("obtained through the following algorithm:", body_style))
    elements.append(t_algo)
    elements.append(Paragraph("(Hash report to be enclosed with the certificate)", body_style))
    elements.append(Spacer(1, 4))

    # Part B Signatory block MUST remain blank
    elements.append(Paragraph("(Name, designation and signature)", body_style))
    elements.append(Paragraph("Date (DD/MM/YYYY): _____", body_style))
    elements.append(Paragraph("Time (IST): ________hours (In 24 hours format)", body_style))
    elements.append(Paragraph("Place: ____________", body_style))

    # ==================== ANNEXURE: HASH REPORT ====================
    if mode == "prefilled" and report_data:
        elements.append(PageBreak())
        elements.append(Paragraph("ANNEXURE 1: HASH REPORT", title_style))
        elements.append(Paragraph("(Enclosed with Section 63 Certificate Part A and Part B)", subtitle_style))
        elements.append(Spacer(1, 6))

        cert_id = report_data.get("certificate_id", "CERT-PENDING")
        bundle_id = report_data.get("bundle_id", "BUNDLE-PENDING")
        elements.append(Paragraph(f"<b>Certificate ID:</b> {cert_id} &nbsp;|&nbsp; <b>Bundle ID:</b> {bundle_id}", bold_style))
        elements.append(Paragraph(f"<b>Bundle Manifest SHA-256:</b> <code>{manifest_hash}</code>", body_style))
        elements.append(Paragraph(f"<b>Tool Version:</b> ChainNetra {report_data.get('tool_version', '1.0.0')} &nbsp;|&nbsp; <b>Git Commit:</b> {report_data.get('git_commit', 'HEAD')}", body_style))
        elements.append(Spacer(1, 8))

        elements.append(Paragraph("Forensic Artifacts Cryptographic Hash Inventory:", bold_style))
        art_rows = [["Artifact File", "Size", "SHA-256 Hash", "Captured (UTC)"]]
        for art in report_data.get("artifacts", []):
            art_rows.append([
                art.get("filename", "")[:28],
                f"{art.get('size_bytes', 0):,} B",
                art.get("sha256", "")[:32] + "...",
                art.get("captured_at", "")[:19]
            ])

        t_art = Table(art_rows, colWidths=[150, 70, 200, 120])
        t_art.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 7),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(t_art)
        elements.append(Spacer(1, 8))

        # On-chain facts for direct re-verification
        onchain = report_data.get("on_chain_facts", [])
        if onchain:
            elements.append(Paragraph("On-Chain Cryptographic Facts (Directly Re-verifiable on Public Ledgers):", bold_style))
            oc_rows = [["Chain", "Transaction Hash", "Block Number"]]
            for oc in onchain:
                oc_rows.append([
                    oc.get("chain", "").upper(),
                    oc.get("tx_hash", ""),
                    str(oc.get("block_number", ""))
                ])
            t_oc = Table(oc_rows, colWidths=[80, 360, 100])
            t_oc.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 7),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ]))
            elements.append(t_oc)

    # Build PDF with custom canvas supporting watermarking and numbering
    def make_canvas(*args, **kwargs):
        return NumberedCanvasWithWatermark(*args, watermark_text=watermark, **kwargs)

    doc.build(elements, canvasmaker=make_canvas)
    return output_path
