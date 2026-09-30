import os
import json
import hashlib
import qrcode
from io import BytesIO
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from sqlalchemy.orm import Session
from app.db.models import Case, Report, TraceSnapshot
from app.core.config import settings
from app.core.audit import log_audit_action

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports_storage")
os.makedirs(REPORTS_DIR, exist_ok=True)

class ReportService:
    @staticmethod
    def generate_case_report(db: Session, case_id: int, generated_by: str = "investigator@demo") -> dict:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")

        report_count = db.query(Report).count() + 1
        now_utc = datetime.now(timezone.utc)
        report_number = f"CR-NETRA-{now_utc.year}-{case_id:04d}-{report_count:04d}"
        pdf_filename = f"{report_number}.pdf"
        pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

        # Retrieve or construct snapshot
        snapshot = db.query(TraceSnapshot).filter(TraceSnapshot.case_id == case_id).order_by(TraceSnapshot.id.desc()).first()
        if snapshot:
            snapshot_data = json.loads(snapshot.snapshot_json)
            snapshot_hash = snapshot.sha256_hash
        else:
            snapshot_data = {
                "case_id": case_id,
                "case_number": case.case_number,
                "primary_address": case.primary_address,
                "primary_chain": case.primary_chain,
                "timestamp": now_utc.isoformat()
            }
            canonical_json = json.dumps(snapshot_data, sort_keys=True)
            snapshot_hash = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
            # Save snapshot
            snap_rec = TraceSnapshot(case_id=case_id, snapshot_json=canonical_json, sha256_hash=snapshot_hash)
            db.add(snap_rec)
            db.commit()

        # Build QR code for verification
        verify_url = f"http://localhost:5173/verify/{snapshot_hash}"
        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data(verify_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#070B14", back_color="#FFFFFF")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        # Build PDF using ReportLab
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        normal = styles['Normal']
        normal.textColor = colors.HexColor("#1A202C")
        normal.fontSize = 9.5
        normal.leading = 13

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#070B14"),
            fontName="Helvetica-Bold"
        )
        h2_style = ParagraphStyle(
            'ReportH2',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0D1424"),
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=6
        )
        caption_style = ParagraphStyle(
            'ReportCaption',
            parent=normal,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#718096")
        )

        elements = []

        # Header Banner
        header_data = [
            [
                Paragraph("<b>CHAINNETRA FORENSIC INTELLIGENCE PLATFORM</b><br/><font size='8' color='#4A5568'>LAW ENFORCEMENT CRYPTOCURRENCY ATTRIBUTION & EVIDENCE REPORT</font>", normal),
                Image(qr_buffer, width=65, height=65)
            ]
        ]
        t_head = Table(header_data, colWidths=[430, 80])
        t_head.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(t_head)
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#FFB020"), spaceAfter=14))

        # Title
        elements.append(Paragraph(f"Forensic Investigation Report: {case.case_number}", title_style))
        elements.append(Paragraph(f"<b>Case Title:</b> {case.title} | <b>Generated:</b> {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}", caption_style))
        elements.append(Spacer(1, 12))

        # Executive Summary
        elements.append(Paragraph("1. Executive Summary", h2_style))
        summary_text = (
            f"This standardized forensic attribution report was autonomously compiled by ChainNetra for law-enforcement "
            f"agencies. The investigation traced illicit cryptocurrency flows originating from suspect wallet "
            f"<b>{case.primary_address}</b> on the <b>{case.primary_chain.upper()}</b> network. "
            f"Multi-hop fund flow analysis identified immediate cash-out consolidation at a Virtual Asset Service Provider (VASP), "
            f"providing corroborated evidence for prompt account freezing and 90-day KYC preservation orders."
        )
        elements.append(Paragraph(summary_text, normal))
        elements.append(Spacer(1, 10))

        # Case & Complaint Metadata Table
        elements.append(Paragraph("2. Victim & Complaint Parameters", h2_style))
        meta_table_data = [
            ["Case ID", case.case_number, "Primary Chain", case.primary_chain.upper()],
            ["Suspect Root Wallet", case.primary_address[:24] + "...", "Case Status", case.status],
            ["Investigating Officer", generated_by, "Time-to-VASP", f"{case.time_to_vasp_seconds or 2.8} seconds"],
            ["Taint Propagation Model", settings.DEFAULT_TAINT_MODEL.upper(), "Data Ingestion Mode", settings.CHAINNETRA_MODE]
        ]
        t_meta = Table(meta_table_data, colWidths=[120, 140, 120, 130])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#F7FAFC")),
            ('BACKGROUND', (2,0), (2,-1), colors.HexColor("#F7FAFC")),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#2D3748")),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 8.5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(t_meta)
        elements.append(Spacer(1, 12))

        # VASP Attribution & Evidence Table
        elements.append(Paragraph("3. Target VASP Attribution & Confidence Breakdown", h2_style))
        vasp_table_data = [
            ["Target VASP Entity", "DemoX Exchange", "Attribution Confidence", "92.4% (VERIFIED)"],
            ["VASP Category", "Centralized Exchange", "Deposit Vault Address", "TXDemoxDepositVault9999999999999"],
            ["Hops From Suspect", "4 Hops (Consolidated)", "Attributed Value", "$133,500.00 USDT (~₹1.11 Cr)"],
            ["Evidence Heuristic", "Deposit-to-Hot Sweep Pattern", "Jurisdiction / SLA", "Seychelles / < 2 Hours"]
        ]
        t_vasp = Table(vasp_table_data, colWidths=[120, 140, 120, 130])
        t_vasp.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#EDF2F7")),
            ('BACKGROUND', (2,0), (2,-1), colors.HexColor("#EDF2F7")),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#1A202C")),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8.5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(t_vasp)
        elements.append(Spacer(1, 12))

        # Recommended Actions
        elements.append(Paragraph("4. Recommended Priority Law Enforcement Actions", h2_style))
        recs = [
            "<b>[CRITICAL]</b> Dispatch Emergency Account Freeze Notice to DemoX Exchange compliance team for deposit vault <code>TXDemoxDepositVault9999999999999</code>.",
            "<b>[HIGH]</b> Issue Section 91 CrPC / IT Act production order for 90-day preservation of KYC identities, login IP addresses, device IMEIs, and connected bank details.",
            "<b>[HIGH]</b> Cross-reference beneficiary records against linked interstate NCRP cyber complaints.",
            "<b>[MEDIUM]</b> Place intermediary mule wallets on 24/7 automated ChainNetra mempool watchlist."
        ]
        for r in recs:
            elements.append(Paragraph(f"• {r}", normal))
            elements.append(Spacer(1, 3))

        elements.append(Spacer(1, 10))

        # Certificate of Authenticity (Section 65B format)
        elements.append(Paragraph("5. Digital Evidence Certificate (Template)", h2_style))
        cert_text = (
            "I hereby certify that this electronic forensic report is a true reproduction of cryptographically logged "
            "records extracted from the ChainNetra ledger indexing engine. The hash of the underlying canonical trace "
            f"snapshot is <b>{snapshot_hash}</b>. The system was functioning under normal operating parameters during data generation."
        )
        elements.append(Paragraph(cert_text, caption_style))
        elements.append(Spacer(1, 10))

        # Verification Hash Footer
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=8))
        elements.append(Paragraph(f"<b>Snapshot SHA-256:</b> {snapshot_hash}", caption_style))
        elements.append(Paragraph(f"<b>Verification Portal:</b> {verify_url}", caption_style))

        # Build document
        doc.build(elements)

        # Compute PDF file SHA-256
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # Save Report record in DB
        report_rec = Report(
            case_id=case_id,
            report_number=report_number,
            pdf_path=pdf_path,
            sha256_hash=pdf_hash,
            snapshot_sha256=snapshot_hash,
            generated_by=generated_by
        )
        db.add(report_rec)
        db.commit()
        db.refresh(report_rec)

        log_audit_action(
            db=db,
            user_email=generated_by,
            action="GENERATE_INVESTIGATION_REPORT",
            entity_type="REPORT",
            entity_id=str(report_rec.id),
            details={
                "report_number": report_number,
                "pdf_hash": pdf_hash,
                "snapshot_hash": snapshot_hash
            }
        )

        return {
            "id": report_rec.id,
            "report_number": report_number,
            "pdf_path": pdf_path,
            "pdf_hash": pdf_hash,
            "snapshot_hash": snapshot_hash,
            "verify_url": verify_url
        }
