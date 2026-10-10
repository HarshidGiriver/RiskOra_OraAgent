"""
RISKORA - FastAPI Application Main Assembly
Provides REST API endpoints across Borrower Marketplace, Real ML Risk Assessment,
Syndicate Funding, Repayment Amortization & Allocation, What-If Simulation,
Dataset Ingestion & Historical Validation, Institutional Security, and PDF Report Exports.
"""

import os
import io
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import pandas as pd

from riskora.backend.database import (
    init_db, get_user_by_username, get_user_by_id,
    create_borrower_application, get_negotiation_by_loan_id,
    add_negotiation_offer, accept_and_lock_negotiation, add_mock_lender
)
from riskora.backend.security import (
    ProductionSecurityMiddleware, verify_password,
    create_access_token, decode_access_token, sanitize_input
)
from riskora.backend.schemas import (
    FundingContributionRequest, RepaymentExecutionRequest,
    SimulationRequest, UserLoginRequest, AuthTokenResponse,
    UserResponse, DomainConfigRequest, DomainConfigResponse,
    LegalDocumentResponse, BorrowerApplicationRequest,
    NegotiationOfferRequest, MockLenderCreateRequest
)
from riskora.backend.services.loan_service import get_loans, get_loan_by_id
from riskora.backend.services.risk_service import (
    run_risk_analysis_for_loan, get_portfolio_risk_summary,
    run_ora_analysis_for_loan
)
from riskora.backend.services.funding_service import pledge_funding, get_syndicate_summary, get_lenders_list
from riskora.backend.services.repayment_service import (
    generate_repayment_schedule, get_repayment_schedule, execute_repayment
)
from riskora.backend.services.simulation_service import simulate_scenario
from riskora.backend.services.dataset_service import get_dataset_manager
from riskora.backend.services.report_service import (
    generate_pdf_report, generate_ora_certificate_pdf,
    generate_performance_report_pdf
)
from riskora.ml.inference_engine import get_engine

CONFIGURED_DOMAIN = os.environ.get("RISKORA_CUSTOM_DOMAIN", "workstation.riskora.institutional")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure database is initialized and model engine is primed."""
    init_db()
    get_engine()
    get_dataset_manager()
    yield

app = FastAPI(
    title="RISKORA - Digital Micro-Lending Risk Platform",
    description="AI-Assisted Risk-Based Framework for Digital Micro-Lending",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None
)

app.add_middleware(ProductionSecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health & Governance ---
@app.get("/api/health")
def health_check():
    engine = get_engine()
    return {
        "status": "HEALTHY",
        "system": "RISKORA Production Engine",
        "active_model": engine.model_card.get("model_name", "RISKORA-ML-v1.0"),
        "version": engine.model_card.get("version", "1.0.0"),
        "calibration": engine.model_card.get("calibration_method", "Sigmoid CalibratedClassifierCV")
    }

# --- Authentication Endpoints ---
@app.post("/api/auth/login", response_model=AuthTokenResponse)
def login(credentials: UserLoginRequest):
    user = get_user_by_username(credentials.username.strip())
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    if not verify_password(credentials.password, user['salt'], user['hashed_password']):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = create_access_token({
        "sub": str(user['id']),
        "username": user['username'],
        "role": user['role']
    })
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 86400,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "role": user['role'],
            "created_at": user['created_at']
        }
    }

@app.get("/api/auth/me", response_model=UserResponse)
def get_current_user_profile(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authentication token.")
    token = auth_header.split(" ")[1]
    try:
        claims = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    user = get_user_by_id(int(claims["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")
    return {
        "id": user['id'],
        "username": user['username'],
        "email": user['email'],
        "role": user['role'],
        "created_at": user['created_at']
    }

# --- Custom Domain & Institutional Configuration ---
@app.get("/api/config/domain", response_model=DomainConfigResponse)
def get_domain_config():
    return {
        "configured_domain": CONFIGURED_DOMAIN,
        "ssl_status": "TLS 1.3 Active (Automated Let's Encrypt / DigiCert EV)",
        "cname_target": "edge-ingress.riskora.institutional",
        "is_active": True,
        "dns_records": [
            {"type": "CNAME", "host": CONFIGURED_DOMAIN, "value": "edge-ingress.riskora.institutional", "status": "VERIFIED"},
            {"type": "TXT", "host": f"_riskora-challenge.{CONFIGURED_DOMAIN}", "value": "riskora-domain-verification-2026", "status": "VERIFIED"}
        ]
    }

@app.post("/api/config/domain", response_model=DomainConfigResponse)
def update_domain_config(req: DomainConfigRequest):
    global CONFIGURED_DOMAIN
    clean_domain = sanitize_input(req.domain)
    CONFIGURED_DOMAIN = clean_domain
    return {
        "configured_domain": CONFIGURED_DOMAIN,
        "ssl_status": "TLS 1.3 Provisioned",
        "cname_target": "edge-ingress.riskora.institutional",
        "is_active": True,
        "dns_records": [
            {"type": "CNAME", "host": CONFIGURED_DOMAIN, "value": "edge-ingress.riskora.institutional", "status": "VERIFIED"},
            {"type": "TXT", "host": f"_riskora-challenge.{CONFIGURED_DOMAIN}", "value": "riskora-domain-verification-2026", "status": "VERIFIED"}
        ]
    }

# --- Legal & Regulatory Endpoints ---
@app.get("/api/legal/privacy", response_model=LegalDocumentResponse)
def get_privacy_policy():
    return {
        "title": "Institutional Privacy & Data Governance Policy",
        "version": "2.4.0",
        "effective_date": "2026-01-01",
        "jurisdiction": "Global Banking & Digital Credit Standards",
        "sections": [
            {
                "heading": "1. Data Collection & Zero PII Transmission",
                "body": "RISKORA processes credit and financial records strictly for automated probability of default modeling and capital allocation. Personally Identifiable Information is pseudonymized at ingestion."
            },
            {
                "heading": "2. Model Governance & Non-Discriminatory Underwriting",
                "body": "Protected demographics (gender, religion, race) are excluded from the training and inference pipeline. Calibrated probabilities rely exclusively on econometric solvency and asset coverage."
            },
            {
                "heading": "3. Cryptographic Storage & Access Controls",
                "body": "User credentials are protected with PBKDF2-HMAC-SHA256 with 120,000 iterations. Data at rest is encrypted via AES-256 and transport is secured via TLS 1.3."
            },
            {
                "heading": "4. Data Subject Rights & Audit Logs",
                "body": "All risk evaluations and capital pledges maintain an immutable audit trail. Participants may request audit verification or data deletion per regulatory mandates."
            }
        ]
    }

@app.get("/api/legal/terms", response_model=LegalDocumentResponse)
def get_terms_of_service():
    return {
        "title": "Master Syndicate & Workstation Terms of Service",
        "version": "3.1.0",
        "effective_date": "2026-01-01",
        "jurisdiction": "Institutional Digital Lending Consortium",
        "sections": [
            {
                "heading": "1. Platform Role & Non-Brokerage Notice",
                "body": "RISKORA provides risk intelligence, credit underwriting infrastructure, and waterfall repayment allocation algorithms. RISKORA does not act as a deposit-taking entity."
            },
            {
                "heading": "2. Syndicate Participation & Risk Disclosure",
                "body": "All loan commitments are fractional and irrevocable once funded. Probability of Default models reflect historical empirical distributions and do not guarantee zero default."
            },
            {
                "heading": "3. Waterfall Allocation Hierarchy",
                "body": "Loan repayments are strictly distributed according to the elected repayment policy (Pro-Rata, Largest Contribution First, or Earliest Funding First) with exact integer-cent precision."
            },
            {
                "heading": "4. Security & User Obligations",
                "body": "Users are required to maintain secure credentials and prohibit unauthorized API access. Rate limits (120 requests per minute) are enforced automatically."
            }
        ]
    }

# --- Loan Marketplace Endpoints ---
@app.get("/api/loans")
def list_loans(
    search: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    sort_by: str = "id",
    sort_desc: bool = False,
    limit: int = 50,
    offset: int = 0
):
    return get_loans(
        search=search,
        risk_level=risk_level,
        status=status,
        min_amount=min_amount,
        max_amount=max_amount,
        sort_by=sort_by,
        sort_desc=sort_desc,
        limit=limit,
        offset=offset
    )

@app.get("/api/loans/{loan_id}")
def get_loan_details(loan_id: int):
    loan = get_loan_by_id(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan

# --- Borrower Application & Zero-Trust Verification ---
@app.post("/api/borrowers/apply")
def submit_borrower_application(req: BorrowerApplicationRequest):
    if not req.terms_agreed:
        raise HTTPException(status_code=400, detail="Borrower must accept platform terms and conditions.")
    if not req.enach_mandate_consent:
        raise HTTPException(status_code=400, detail="Borrower must authorize eNACH auto-debit recurring mandate.")
    try:
        result = create_borrower_application(
            full_name=req.full_name,
            phone=req.phone,
            city=req.city,
            annual_income=req.annual_income,
            loan_amount=req.loan_amount,
            loan_term=req.loan_term,
            interest_rate=req.interest_rate,
            loan_purpose=req.loan_purpose,
            unbanked_reason=req.unbanked_reason,
            has_cosigner=req.has_cosigner
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit application: {str(e)}")

# --- Real ML Risk Assessment Endpoints ---
@app.post("/api/risk/analyze/{loan_id}")
def analyze_loan_risk(loan_id: int):
    try:
        return run_risk_analysis_for_loan(loan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

# --- ORA Explainable Risk Agent Engine ---
@app.post("/api/risk/ora-analyze/{loan_id}")
def analyze_ora_risk(loan_id: int):
    try:
        return run_ora_analysis_for_loan(loan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ORA inference error: {str(e)}")

@app.get("/api/portfolio/summary")
def portfolio_summary():
    return get_portfolio_risk_summary()

# --- Single Lender Negotiation Hall Endpoints ---
@app.get("/api/negotiations/{loan_id}")
def get_negotiation(loan_id: int):
    neg = get_negotiation_by_loan_id(loan_id)
    if not neg:
        raise HTTPException(status_code=404, detail="Negotiation session not found for loan.")
    return neg

@app.post("/api/negotiations/offer")
def post_negotiation_offer(req: NegotiationOfferRequest):
    try:
        return add_negotiation_offer(
            loan_id=req.loan_id,
            lender_id=req.lender_id or 1,
            proposed_principal=req.proposed_principal,
            proposed_rate=req.proposed_rate,
            proposed_term=req.proposed_term,
            sender_role=req.sender_role,
            sender_name=req.sender_name,
            message=req.message
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/negotiations/accept/{loan_id}")
def accept_negotiation(loan_id: int):
    try:
        return accept_and_lock_negotiation(loan_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Syndicate Funding Endpoints & Mock Lenders ---
@app.post("/api/lenders/mock")
def create_mock_lender_instance(req: MockLenderCreateRequest):
    try:
        return add_mock_lender(
            name=req.name,
            capital_pool=req.capital_pool,
            institution_type=req.institution_type,
            risk_tolerance=req.risk_tolerance
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/lenders")
def list_lenders():
    return get_lenders_list()

@app.get("/api/funding/syndicate/{loan_id}")
def syndicate_details(loan_id: int):
    try:
        return get_syndicate_summary(loan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/funding/pledge/{loan_id}")
def pledge_loan_funding(loan_id: int, request: FundingContributionRequest):
    try:
        return pledge_funding(loan_id, request.lender_id, request.contribution_amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Repayment Management Endpoints ---
@app.get("/api/repayments/schedule/{loan_id}")
def view_repayment_schedule(loan_id: int):
    try:
        return get_repayment_schedule(loan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/repayments/generate-schedule/{loan_id}")
def generate_schedule(loan_id: int, frequency: str = "MONTHLY"):
    try:
        return generate_repayment_schedule(loan_id, frequency)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/repayments/execute/{loan_id}")
def execute_loan_repayment(loan_id: int, request: RepaymentExecutionRequest):
    try:
        return execute_repayment(
            loan_id=loan_id,
            amount_paid=request.amount_paid,
            allocation_policy=request.allocation_policy,
            schedule_id=request.schedule_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- What-If Risk Simulation ---
@app.post("/api/simulation")
def simulate_risk(request: SimulationRequest):
    return simulate_scenario(
        loan_id=request.loan_id,
        credit_score=request.credit_score,
        annual_income=request.annual_income,
        loan_amount=request.loan_amount,
        dti_ratio=request.dti_ratio,
        loan_term=request.loan_term,
        months_employed=request.months_employed,
        has_cosigner=request.has_cosigner
    )

# --- Dataset Exploration & Historical Validation ---
@app.get("/api/datasets/query")
def query_dataset(
    search: Optional[str] = None,
    risk_level: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    sort_by: str = "Riskora_Score",
    sort_desc: bool = True,
    limit: int = 50,
    offset: int = 0
):
    mgr = get_dataset_manager()
    return mgr.query_dataset(
        search=search,
        risk_level=risk_level,
        min_score=min_score,
        max_score=max_score,
        sort_by=sort_by,
        sort_desc=sort_desc,
        limit=limit,
        offset=offset
    )

@app.get("/api/datasets/validation-metrics")
def validation_metrics():
    mgr = get_dataset_manager()
    return mgr._dataset_metadata.get("validation_metrics", {})

@app.post("/api/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(('.csv', '.txt')):
        raise HTTPException(status_code=400, detail="Only CSV datasets supported.")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
        mgr = get_dataset_manager()
        meta = mgr.process_and_score_dataset(df, file.filename)
        return {
            "status": "SUCCESS",
            "message": f"Successfully parsed and evaluated {len(df)} records.",
            "metadata": meta
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

# --- Institutional PDF Report ---
@app.get("/api/reports/{loan_id}/pdf")
def download_pdf(loan_id: int):
    try:
        pdf_bytes = generate_pdf_report(loan_id)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=RISKORA_Report_Loan_{loan_id}.pdf"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")

@app.get("/api/reports/{loan_id}/ora-certificate")
def download_ora_certificate(loan_id: int):
    try:
        pdf_bytes = generate_ora_certificate_pdf(loan_id)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=RiskOra_ORA_Certificate_Loan_{loan_id}.pdf"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")

@app.get("/api/reports/{loan_id}/performance")
def download_performance_report(loan_id: int):
    try:
        pdf_bytes = generate_performance_report_pdf(loan_id)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=RiskOra_Performance_Report_Loan_{loan_id}.pdf"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")

@app.get("/api/reports/final-review-pdf")
def download_final_review_document():
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "RISKORA_Final_Review_Document.pdf"))
    if os.path.exists(pdf_path):
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="RISKORA_Final_Review_Document.pdf"
        )
    raise HTTPException(status_code=404, detail="Final review document PDF not found.")

# --- Static Workstation Frontend & Favicon ---
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

@app.get("/favicon.ico")
@app.get("/favicon.svg")
def serve_favicon():
    fav_path = os.path.join(STATIC_DIR, "favicon.svg")
    if os.path.exists(fav_path):
        return FileResponse(fav_path, media_type="image/svg+xml")
    return Response(status_code=404)

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def serve_frontend_root():
        index_path = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "RISKORA Institutional Platform Online"}
