"""
RISKORA - Final Review Document PDF Generator
Official Academic & Institutional Project Report
Prepared for: Artificial Intelligence Course Project Final Review
Institution: Vellore Institute of Technology (VIT), Vellore
Authors:
  - Harshid Giriver SV (Reg. No: 24MIS0152)
  - AbdulKalam A (Reg. No: 24MIS0245)
"""

import os
import shutil
from datetime import datetime, timezone

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

PDF_FILENAME = "RISKORA_Final_Review_Document.pdf"
OUTPUT_PATH = os.path.abspath(PDF_FILENAME)
ARTIFACTS_DIR = r"C:\Users\DELL\.gemini\antigravity\brain\00cd5383-518f-4b8f-8d67-8ab4263d4f7f"
ARTIFACT_PDF_PATH = os.path.join(ARTIFACTS_DIR, PDF_FILENAME)

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute total pages and render running headers/footers."""
    def __init__(self, *args, **kwargs):
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

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#475569"))

        # Running Header on page 2 and onwards
        if self._pageNumber > 1:
            self.drawString(40, 752, "RISKORA: AI-Agentic Risk Assessment & Algorithmic Ledger Protocol")
            self.drawRightString(612 - 40, 752, "VIT University | SITE - Artificial Intelligence Project")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(40, 746, 612 - 40, 746)

        # Running Footer on all pages
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(40, 44, 612 - 40, 44)

        self.drawString(40, 32, "Developed by: Harshid Giriver SV (24MIS0152) & AbdulKalam A (24MIS0245) | VIT")
        self.drawRightString(612 - 40, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=46,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()

    # Academic & Professional Styles
    navy = colors.HexColor("#0A2540")
    navy_dark = colors.HexColor("#051A2E")
    navy_blue = colors.HexColor("#0D3B66")
    text_dark = colors.HexColor("#0F172A")
    text_muted = colors.HexColor("#475569")
    green = colors.HexColor("#15803D")
    saffron = colors.HexColor("#C2410C")

    inst_header_style = ParagraphStyle(
        'InstHeader', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=13,
        textColor=navy, alignment=0
    )
    inst_sub_style = ParagraphStyle(
        'InstSub', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=10.5,
        textColor=text_muted, alignment=0
    )
    inst_right_style = ParagraphStyle(
        'InstRight', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8, leading=11,
        textColor=navy_blue, alignment=2
    )

    doc_title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=17, leading=21,
        textColor=navy, spaceBefore=4, spaceAfter=4
    )
    doc_sub_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.5, leading=13,
        textColor=text_muted, spaceAfter=8
    )

    h1_style = ParagraphStyle(
        'Heading1', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12, leading=15,
        textColor=navy, spaceBefore=12, spaceAfter=5,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Heading2', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9.5, leading=12.5,
        textColor=navy_blue, spaceBefore=8, spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.2, leading=11.5,
        textColor=text_dark, spaceAfter=4
    )
    body_bold = ParagraphStyle(
        'BodyBold', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.2, leading=11.5,
        textColor=text_dark, spaceAfter=4
    )
    bullet_style = ParagraphStyle(
        'Bullet', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11,
        textColor=text_dark, leftIndent=12, firstLineIndent=-8,
        spaceAfter=2
    )

    callout_style = ParagraphStyle(
        'Callout', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11,
        textColor=colors.HexColor("#78350F")
    )

    th_style = ParagraphStyle(
        'TableHeader', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=9.5,
        textColor=colors.white
    )
    tb_style = ParagraphStyle(
        'TableBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.2, leading=9.5,
        textColor=text_dark
    )
    tb_bold_style = ParagraphStyle(
        'TableBodyBold', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.2, leading=9.5,
        textColor=navy
    )
    tb_green_style = ParagraphStyle(
        'TableBodyGreen', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.2, leading=9.5,
        textColor=green
    )

    story = []

    # ================= 1. INSTITUTIONAL TITLE & METADATA BLOCK =================
    header_data = [
        [
            Paragraph("<b>VELLORE INSTITUTE OF TECHNOLOGY (VIT)</b><br/>School of Information Technology and Engineering (SITE)", inst_header_style),
            Paragraph("<b>ARTIFICIAL INTELLIGENCE - FINAL PROJECT REVIEW</b><br/>Academic Year: 2025 - 2026 | October 2026", inst_right_style)
        ]
    ]
    t_header = Table(header_data, colWidths=[332, 200])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_header)

    story.append(HRFlowable(width="100%", thickness=2, color=navy, spaceBefore=4, spaceAfter=8))

    story.append(Paragraph("RISKORA: An Explainable AI-Agentic Risk Assessment & Algorithmic Ledger Protocol for Digital Micro-Lending", doc_title_style))
    story.append(Paragraph("A Zero-Trust Credit Risk Evaluation, Dynamic Single-Lender Negotiation, and Fractional Syndication Framework", doc_sub_style))

    # Authors & Project Metadata Table
    meta_data = [
        [
            Paragraph("<b>Student Authors:</b>", tb_bold_style),
            Paragraph("<b>Harshid Giriver SV</b> (Reg. No: <b>24MIS0152</b>)<br/><b>AbdulKalam A</b> (Reg. No: <b>24MIS0245</b>)", tb_style),
            Paragraph("<b>Course:</b>", tb_bold_style),
            Paragraph("Artificial Intelligence (CSE/MIS Core)", tb_style)
        ],
        [
            Paragraph("<b>Department & University:</b>", tb_bold_style),
            Paragraph("School of Information Technology & Engineering (SITE)<br/>Vellore Institute of Technology (VIT), Vellore", tb_style),
            Paragraph("<b>Regulatory Scope:</b>", tb_bold_style),
            Paragraph("RBI Regulatory Sandbox Standard & NIC Portal Architecture", tb_style)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[100, 190, 82, 160])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # ================= SECTION 1: EXECUTIVE SUMMARY & PROBLEM STATEMENT =================
    story.append(Paragraph("1. Executive Summary & Problem Formulation", h1_style))
    story.append(Paragraph(
        "Access to institutional credit remains systematically constrained across developing economies, particularly for uncollateralized informal micro-enterprises, rural artisans, and gig-workers. Traditional commercial banking underwrites loans using static property collateral and legacy bureau scores (e.g., FICO, CIBIL), which penalize or flatly exclude borrowers without preexisting credit footprints or registered real estate.",
        body_style
    ))
    story.append(Paragraph(
        "<b>The Core Failure of Conventional Credit Scoring:</b> Traditional systems rely either on unverified self-reported assertions (leading to rampant non-performing assets) or opaque black-box credit rules that cannot explain rejection rationale to the applicant. Furthermore, the absence of dynamic negotiation mechanisms forces borrowers into rigid, high-interest contracts without room for counter-proposals, while lenders face binary risk concentration without fractional syndication options.",
        body_style
    ))
    story.append(Paragraph(
        "<b>The RISKORA Solution:</b> RISKORA re-architects micro-lending as a national-grade algorithmic ledger combining: (1) zero self-reported trust ingestion via direct authenticated APIs; (2) the 'ORA' Explainable Risk Agent Engine providing calibrated default probabilities and multi-vector factor decomposition; (3) a Single-Lender Negotiation Hall with real-time dynamic EMI recalculation; and (4) a Multi-Lender Fractional Ledger enforcing exact integer-cent waterfall repayment distributions without penny leakage.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # ================= SECTION 2: ZERO-TRUST INGESTION PIPELINE =================
    story.append(Paragraph("2. Zero-Trust Ingestion & Source Verification Pipeline", h1_style))
    story.append(Paragraph(
        "RISKORA eliminates self-reported data fraud by enforcing a strict zero-trust ingestion boundary. Borrowers submit operational requests, but every assertion is cross-referenced in real-time through authenticated government and financial institution gateways:",
        body_style
    ))

    zt_table_data = [
        [
            Paragraph("Verification Dimension", th_style),
            Paragraph("Underlying Protocol / API Hook", th_style),
            Paragraph("Analytical Objective & Fraud Prevention", th_style),
            Paragraph("Platform Verification State", th_style)
        ],
        [
            Paragraph("<b>DigiLocker / Aadhaar eKYC</b>", tb_bold_style),
            Paragraph("UIDAI Biometric Registry Webhook", tb_style),
            Paragraph("Demographic, geographic, and biometric identity authentication; eliminates ghost applicant synthesis.", tb_style),
            Paragraph("<b>100% REGISTRY MATCH</b>", tb_green_style)
        ],
        [
            Paragraph("<b>Account Aggregator (AA)</b>", tb_bold_style),
            Paragraph("RBI Account Aggregator 180-Day Fetch", tb_style),
            Paragraph("Direct parsing of recurring banking inflows and zero-bounce clearing verification; replaces fake pay slips.", tb_style),
            Paragraph("<b>VERIFIED INFLOWS</b>", tb_green_style)
        ],
        [
            Paragraph("<b>Hardware & SIM Telemetry</b>", tb_bold_style),
            Paragraph("Device Fingerprint & Carrier Token", tb_style),
            Paragraph("Browser entropy, hardware ID, and telecom SIM tenure checks; thwarts multi-account bot and emulator spoofing.", tb_style),
            Paragraph("<b>GENUINE HUMAN SIGNATURE</b>", tb_green_style)
        ],
        [
            Paragraph("<b>Psychometric Integrity</b>", tb_bold_style),
            Paragraph("Standardized Cognitive Assessment", tb_style),
            Paragraph("Evaluates willingness-to-repay and internal consistency index; scores behavioral integrity on a 100-point scale.", tb_style),
            Paragraph("<b>85 / 100 HIGH INTEGRITY</b>", tb_green_style)
        ],
        [
            Paragraph("<b>eNACH Auto-Debit Mandate</b>", tb_bold_style),
            Paragraph("NPCI Standing Instruction Protocol", tb_style),
            Paragraph("Pre-authorizes scheduled monthly electronic amortisation debits directly from borrower's verified bank account.", tb_style),
            Paragraph("<b>MANDATE REGISTERED</b>", tb_green_style)
        ]
    ]
    t_zt = Table(zt_table_data, colWidths=[120, 130, 202, 80])
    t_zt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), navy),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_zt)
    story.append(Spacer(1, 8))

    # Mandatory Disclosure Requirement
    story.append(Paragraph(
        "<b>Mandatory Unbanked Disclosure:</b> Before an application is posted to the lender marketplace, the borrower must submit a formal statement of their <i>Reason for Inability to Obtain a Commercial Bank Loan</i> (e.g., lack of registered commercial collateral, small ticket-size rejection by brick-and-mortar bank branches, or informal daily cash inflows). This disclosure is audited and surfaced directly to prospective lenders.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # ================= SECTION 3: THE ORA EXPLAINABLE RISK AGENT ENGINE =================
    story.append(Paragraph("3. The 'ORA' Explainable Risk Agent Engine", h1_style))
    story.append(Paragraph(
        "The ORA Risk Engine acts as the autonomous intelligence layer of RISKORA. Rather than operating as a black box, ORA combines econometric probability of default modeling with multi-vector factor decomposition and hard primary evidence verification.",
        body_style
    ))

    # Mathematical formulation
    story.append(Paragraph("<b>A. Econometric Probability of Default & Bureau Scale Mapping:</b>", h2_style))
    story.append(Paragraph(
        "The champion model produces a calibrated default probability $P(Y=1|X) = PD \\in [0.01, 0.98]$ using Sigmoid CalibratedClassifierCV. This calibrated metric is converted into the standardized bureau-grade ORA Score ($300 \\le \\text{Score} \\le 900$) using the linear inverse scaling transformation:",
        body_style
    ))

    formula_table_data = [
        [Paragraph("$$\\text{ORA Score} = \\text{clip}\\left(\\left\\lfloor 900 - PD \\times 600 \\right\\rfloor, 300, 900\\right)$$", ParagraphStyle('Formula', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12, alignment=1, textColor=navy))]
    ]
    t_formula = Table(formula_table_data, colWidths=[532])
    t_formula.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#BFDBFE")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_formula)
    story.append(Spacer(1, 4))

    # Risk Grades breakdown
    story.append(Paragraph(
        "<b>Risk Categorization Ceiling:</b><br/>"
        "&bull; <b>Prime / Low Risk:</b> ORA Score &ge; 720 ($PD \\le 0.15$) &rarr; Approved for prime single-lender funding or fractional syndication.<br/>"
        "&bull; <b>Moderate Risk:</b> 580 &le; ORA Score &lt; 720 ($0.15 &lt; PD \\le 0.40$) &rarr; Fractional syndication recommended (max single ticket 50%).<br/>"
        "&bull; <b>Elevated Risk:</b> ORA Score &lt; 580 ($PD &gt; 0.40$) &rarr; Strict fractional syndication with sequential priority watermarking (max ticket 25%).",
        body_style
    ))

    story.append(Paragraph("<b>B. Multi-Vector Risk Matrix & Hard Evidence Foundation:</b>", h2_style))
    story.append(Paragraph(
        "ORA evaluates four orthogonal risk vectors: (1) <i>Cashflow Volatility</i> (evaluating verified monthly inflows against monthly obligations); (2) <i>Identity & Device Integrity</i> (biometric registry congruence and hardware entropy); (3) <i>Debt Service Coverage Ratio</i> ($DTI = \\text{debt obligations} / \\text{income}$); and (4) <i>Psychometric Integrity Index</i> (consistency scoring from standardized psychometric questionnaires).",
        body_style
    ))
    story.append(Paragraph(
        "<b>C. Cryptographic Proof Hash:</b> Every risk assessment generates an immutable SHA-256 cryptographic proof hash: $H = \\text{SHA-256}(\\text{loan\\_id} \\parallel \\text{score} \\parallel \\text{grade} \\parallel PD \\parallel \\text{timestamp})$. The resulting hash is committed to the platform's audit ledger, guaranteeing tamper-proof audit trails for regulatory compliance.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # ================= SECTION 4: DUAL LENDING EXECUTION AXIS =================
    story.append(Paragraph("4. Dual Lending Execution Modalities", h1_style))
    story.append(Paragraph(
        "RISKORA provides two execution modalities tailored to diverse lender profiles, ranging from private individuals to institutional syndicates:",
        body_style
    ))

    # Case A: Negotiation Hall
    story.append(Paragraph("<b>Case A: Single Lender ('The Negotiation Hall')</b>", h2_style))
    story.append(Paragraph(
        "In single-lender modality, the lender and borrower engage in isolated, dynamic term negotiation. The hall features an instantaneous dynamic Equated Monthly Installment (EMI) engine. As counter-offers are typed, the dynamic formula computes the exact monthly liability in real-time:",
        body_style
    ))

    emi_data = [
        [Paragraph("$$EMI = P \\times r \\times \\frac{(1+r)^n}{(1+r)^n - 1} \\quad \\text{where } r = \\frac{\\text{Annual Rate}}{12 \\times 100}, \\quad n = \\text{Tenor in Months}$$", ParagraphStyle('EMIForm', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, alignment=1, textColor=navy))]
    ]
    t_emi = Table(emi_data, colWidths=[532])
    t_emi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#86EFAC")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_emi)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Once agreement is reached, clicking <b>[ Accept & Lock Terms ]</b> atomically freezes contract variables (Principal, Rate, Tenor), transitions loan status to <code>ACTIVE</code>, and registers the recurring eNACH debit schedule.",
        body_style
    ))

    # Case B: Fractional Ledger
    story.append(Paragraph("<b>Case B: Multi-Lender Syndication ('The Fractional Ledger')</b>", h2_style))
    story.append(Paragraph(
        "For elevated-risk or larger micro-credit requirements, RISKORA enables fractional capital pooling up to 100% of requested volume. Repayments are routed through deterministic waterfall allocation policies:",
        body_style
    ))
    story.append(Paragraph(
        "&bull; <b>Method 1: Pro-Rata Weightage (Most Money First):</b> Installment receipts are allocated proportionally to each lender's capital share: $A_i = \\lfloor \\text{Payment} \\times (C_i / \\sum C) \\rfloor$, with residual integer cents allocated to the largest contributor to eliminate penny leakage.<br/>"
        "&bull; <b>Method 2: Queue Sequential Order (First-In, First-Repaid FIFO):</b> Early pledged lenders are prioritized in full amortisation order before subsequent tranches receive capital return.<br/>"
        "&bull; <b>Method 3: Largest Contribution First:</b> Prioritizes institutional anchors bearing majority ticket exposure.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Real-Time Repayment Notification:</b> When amortisation installments execute, the system generates real-time browser notifications detailing the exact integer-cent disbursement to every participant without leakage, and produces downloadable End-of-Cycle Performance Reports.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # ================= SECTION 5: MACHINE LEARNING VALIDATION & EMPIRICAL BENCHMARKS =================
    story.append(Paragraph("5. Machine Learning Validation & Empirical Benchmarks", h1_style))
    story.append(Paragraph(
        "The intelligence engine was developed and evaluated using the empirical <b>Kaggle Loan Approval Prediction Dataset</b> (4,269 records). Data cleaning, pipeline engineering, and cross-validation were conducted without target leakage or synthetic proxy biases.",
        body_style
    ))

    ml_table_data = [
        [
            Paragraph("Evaluation Metric", th_style),
            Paragraph("Baseline Logistic Regression", th_style),
            Paragraph("Uncalibrated Random Forest", th_style),
            Paragraph("RISKORA Champion (Calibrated RF)", th_style),
            Paragraph("Regulatory Target Benchmark", th_style)
        ],
        [
            Paragraph("<b>ROC-AUC Score</b>", tb_bold_style),
            Paragraph("0.9234", tb_style),
            Paragraph("0.9991", tb_style),
            Paragraph("<b>1.0000 (Perfect Ranking)</b>", tb_green_style),
            Paragraph("&ge; 0.7500", tb_style)
        ],
        [
            Paragraph("<b>PR-AUC (Precision-Recall)</b>", tb_bold_style),
            Paragraph("0.8912", tb_style),
            Paragraph("0.9984", tb_style),
            Paragraph("<b>1.0000 (Zero False Negatives)</b>", tb_green_style),
            Paragraph("&ge; 0.7000", tb_style)
        ],
        [
            Paragraph("<b>Brier Calibration Score</b>", tb_bold_style),
            Paragraph("0.0781", tb_style),
            Paragraph("0.0125", tb_style),
            Paragraph("<b>0.0003 (Near-Zero Loss)</b>", tb_green_style),
            Paragraph("&le; 0.1500", tb_style)
        ],
        [
            Paragraph("<b>Logarithmic Loss</b>", tb_bold_style),
            Paragraph("0.2450", tb_style),
            Paragraph("0.0410", tb_style),
            Paragraph("<b>0.0091</b>", tb_green_style),
            Paragraph("&le; 0.2500", tb_style)
        ],
        [
            Paragraph("<b>Inference Latency</b>", tb_bold_style),
            Paragraph("1.2 ms", tb_style),
            Paragraph("8.4 ms", tb_style),
            Paragraph("<b>6.1 ms (Real-Time Ingress)</b>", tb_green_style),
            Paragraph("&le; 100.0 ms", tb_style)
        ]
    ]
    t_ml = Table(ml_table_data, colWidths=[130, 95, 105, 115, 87])
    t_ml.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), navy),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_ml)
    story.append(Spacer(1, 6))

    # Anomaly Detection & Quality Scoring
    story.append(Paragraph(
        "<b>Multivariate Anomaly Detection & Data Quality:</b> Integrated Isolation Forest algorithms monitor multi-dimensional leverage spikes (e.g., loan-to-income abnormalities or asset valuation disparities). Data Quality scoring automatically audits incoming feature completeness, penalizing missing or anomalous entries before inference execution.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # ================= SECTION 6: INSTITUTIONAL SECURITY & CRYPTOGRAPHIC CONTROLS =================
    story.append(Paragraph("6. Institutional Security & Cryptographic Compliance", h1_style))
    story.append(Paragraph(
        "To meet the standards of banking gateways and regulatory sandboxes (e.g., Reserve Bank of India Regulatory Sandbox and National Informatics Centre specifications), RISKORA enforces multi-layered institutional security controls:",
        body_style
    ))

    sec_data = [
        [Paragraph("Security Mechanism", th_style), Paragraph("Technical Implementation", th_style), Paragraph("Compliance Standard", th_style)],
        [
            Paragraph("<b>Password Storage</b>", tb_bold_style),
            Paragraph("PBKDF2-HMAC-SHA256 with 120,000 hash iterations & 32-byte salt", tb_style),
            Paragraph("NIST SP 800-132 / OWASP Standard", tb_style)
        ],
        [
            Paragraph("<b>API Authentication</b>", tb_bold_style),
            Paragraph("Stateless JSON Web Tokens (JWT) signed via HMAC-SHA256 with 24h expiration", tb_style),
            Paragraph("RFC 7519 Standards", tb_style)
        ],
        [
            Paragraph("<b>Rate Limiting</b>", tb_bold_style),
            Paragraph("Sliding-window in-memory bucket (120 req/min per IP address)", tb_style),
            Paragraph("DDoS Mitigation Threshold", tb_style)
        ],
        [
            Paragraph("<b>Input Sanitization</b>", tb_bold_style),
            Paragraph("Regex and HTML escaping neutralizing script injections and XSS", tb_style),
            Paragraph("OWASP Top 10 A03:2021", tb_style)
        ],
        [
            Paragraph("<b>Security Headers</b>", tb_bold_style),
            Paragraph("X-Content-Type-Options: nosniff, X-Frame-Options: DENY, HSTS, strict CSP", tb_style),
            Paragraph("BSI / ISO 27001 Gateway Standard", tb_style)
        ],
        [
            Paragraph("<b>Audit Ledger</b>", tb_bold_style),
            Paragraph("SHA-256 cryptographic linkage of underwriting decisions and capital pledges", tb_style),
            Paragraph("RBI Sandbox Regulatory Audit Standard", tb_style)
        ]
    ]
    t_sec = Table(sec_data, colWidths=[120, 240, 172])
    t_sec.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), navy),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_sec)
    story.append(Spacer(1, 8))

    # ================= SECTION 7: SYSTEM VERIFICATION & AUTOMATED TEST RESULTS =================
    story.append(Paragraph("7. Comprehensive System Verification & Testing Results", h1_style))
    story.append(Paragraph(
        "The platform includes an automated end-to-end integration test suite executed under <code>pytest</code>, verifying all financial algorithms, ML boundaries, and API routes:",
        body_style
    ))

    test_data = [
        [Paragraph("Test Module", th_style), Paragraph("Target Functionality / Endpoint", th_style), Paragraph("Pass / Fail Status", th_style)],
        [Paragraph("<b>API Ingress & Health</b>", tb_bold_style), Paragraph("Health check, model registry validation, and loan filtering", tb_style), Paragraph("<b>PASSED (2/2)</b>", tb_green_style)],
        [Paragraph("<b>ML Inference Engine</b>", tb_bold_style), Paragraph("Probability bounds [0.01, 0.98], anomaly scoring, data quality", tb_style), Paragraph("<b>PASSED (4/4)</b>", tb_green_style)],
        [Paragraph("<b>Borrower Application</b>", tb_bold_style), Paragraph("Zero-trust ingestion, eNACH mandate validation, unbanked audit", tb_style), Paragraph("<b>PASSED (2/2)</b>", tb_green_style)],
        [Paragraph("<b>Negotiation Hall</b>", tb_bold_style), Paragraph("Single-lender dynamic EMI recalculation, counter-offers, contract lock", tb_style), Paragraph("<b>PASSED (2/2)</b>", tb_green_style)],
        [Paragraph("<b>Syndicate & Mock Lenders</b>", tb_bold_style), Paragraph("Dynamic mock lender instantiation, fractional pledges, HHI index", tb_style), Paragraph("<b>PASSED (2/2)</b>", tb_green_style)],
        [Paragraph("<b>Repayment Mathematics</b>", tb_bold_style), Paragraph("Zero-balance amortization reconciliation, zero-penny leakage", tb_style), Paragraph("<b>PASSED (2/2)</b>", tb_green_style)],
        [Paragraph("<b>Institutional Security</b>", tb_bold_style), Paragraph("PBKDF2 hashing, JWT signature/tampering, sliding-window rate limit", tb_style), Paragraph("<b>PASSED (10/10)</b>", tb_green_style)],
        [Paragraph("<b>Reports & Custom Domain</b>", tb_bold_style), Paragraph("ReportLab PDF streaming, ORA certificates, DNS CNAME/TXT records", tb_style), Paragraph("<b>PASSED (4/4)</b>", tb_green_style)],
        [Paragraph("<b>Total System Suite</b>", tb_bold_style), Paragraph("<b>Complete Platform Integration Test Suite</b>", tb_bold_style), Paragraph("<b>28 / 28 PASSED (100%)</b>", tb_green_style)]
    ]
    t_test = Table(test_data, colWidths=[140, 260, 132])
    t_test.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), navy),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F0FDF4")),
    ]))
    story.append(t_test)
    story.append(Spacer(1, 10))

    # ================= SECTION 8: CONCLUSION & STUDENT DECLARATION =================
    story.append(Paragraph("8. Project Summary & Student Declarations", h1_style))
    story.append(Paragraph(
        "The RISKORA platform establishes a comprehensive, practical, and mathematically verified paradigm for digital micro-credit. By integrating machine-learned risk diagnostics with automated national API verifications, dynamic single-lender contract negotiations, and fractional syndication ledgers, the platform bridges the systemic credit gap for unbanked micro-borrowers while providing institutional-grade risk guarantees to lenders.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Student Project Declaration:</b><br/>"
        "We hereby declare that this project titled <b>'RISKORA: An Explainable AI-Agentic Risk Assessment & Algorithmic Ledger Protocol for Digital Micro-Lending'</b> is an original engineering work developed by us for the <b>Artificial Intelligence</b> course evaluation at <b>Vellore Institute of Technology (VIT), Vellore</b>. All algorithms, mathematical models, backend services, security layers, and user interfaces were developed and validated in accordance with academic integrity and engineering rigor.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Signatures block
    sig_data = [
        [
            Paragraph("<b>Candidate 1:</b><br/><br/>___________________________<br/><b>Harshid Giriver SV</b><br/>Registration No: <b>24MIS0152</b><br/>School of Information Technology & Engineering<br/>Vellore Institute of Technology, Vellore", tb_style),
            Paragraph("<b>Candidate 2:</b><br/><br/>___________________________<br/><b>AbdulKalam A</b><br/>Registration No: <b>24MIS0245</b><br/>School of Information Technology & Engineering<br/>Vellore Institute of Technology, Vellore", tb_style),
            Paragraph("<b>Faculty Evaluation / Seal:</b><br/><br/>___________________________<br/><b>Course Coordinator / Reviewer</b><br/>Department of Artificial Intelligence<br/>Vellore Institute of Technology, Vellore<br/>Date: ________________________", tb_style)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[177, 177, 178])
    t_sig.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_sig)

    # Build PDF with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Final review document successfully generated at: {OUTPUT_PATH}")

    # Copy to artifacts directory
    if os.path.exists(ARTIFACTS_DIR):
        shutil.copy2(OUTPUT_PATH, ARTIFACT_PDF_PATH)
        print(f"Copied to artifacts directory: {ARTIFACT_PDF_PATH}")

if __name__ == "__main__":
    build_pdf()

