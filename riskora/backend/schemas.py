"""
RISKORA - Pydantic Schemas & DTO Layer
Provides strict validation, data sanitization, and serialization across API domains.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any

# --- Borrower Schemas ---
class BorrowerBase(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    city: str = "Delhi"
    age: int = Field(..., ge=18, le=90)
    education: str
    employment_type: str
    marital_status: str
    annual_income: float = Field(..., gt=0)
    months_employed: int = Field(..., ge=0)
    credit_score: int = Field(..., ge=300, le=850)
    num_credit_lines: int = Field(..., ge=1, le=50)
    has_mortgage: int = Field(0, ge=0, le=1)
    has_dependents: int = Field(0, ge=0, le=1)

class BorrowerCreate(BorrowerBase):
    pass

class BorrowerResponse(BorrowerBase):
    id: int
    borrower_code: str
    created_at: str

# --- Loan Schemas ---
class LoanBase(BaseModel):
    loan_amount: float = Field(..., gt=1000)
    loan_term: int = Field(..., ge=3, le=60)
    interest_rate: float = Field(..., ge=5.0, le=48.0)
    dti_ratio: float = Field(..., ge=0.01, le=2.0)
    loan_purpose: str
    has_cosigner: int = Field(0, ge=0, le=1)
    repayment_frequency: str = "MONTHLY"
    repayment_policy: str = "PRO_RATA"

class LoanCreate(LoanBase):
    borrower_id: int

class LoanResponse(LoanBase):
    id: int
    loan_code: str
    borrower_id: int
    borrower_name: Optional[str] = None
    borrower_city: Optional[str] = None
    borrower_credit_score: Optional[int] = None
    borrower_income: Optional[float] = None
    funded_amount: float
    funding_progress_pct: float
    remaining_amount: float
    status: str
    created_at: str
    analyzed_at: Optional[str] = None
    risk_assessment: Optional[Dict[str, Any]] = None

# --- Risk Assessment Schemas ---
class RiskDriverItem(BaseModel):
    feature: str
    observed_value: str
    benchmark_value: str
    impact_direction: str
    impact_pct: float
    description: str

class DataQualityResult(BaseModel):
    quality_score: int
    available_fields: int
    total_fields: int
    missing_fields: List[str]
    warnings: List[str]
    validation_status: str

class AnomalyResult(BaseModel):
    anomaly_detected: bool
    anomaly_score: float
    anomaly_flags: List[str]
    recommended_review_intensity: str

class RiskAssessmentResponse(BaseModel):
    loan_id: str
    assessment_timestamp: str
    model_version: str
    probability_of_default: float
    probability_pct: float
    risk_score: int
    risk_level: str
    recommended_review_intensity: str
    funding_recommendation: Dict[str, Any]
    risk_drivers: List[RiskDriverItem]
    data_quality: DataQualityResult
    anomaly_analysis: AnomalyResult
    methodology_disclaimer: str

# --- Funding Schemas ---
class FundingContributionRequest(BaseModel):
    lender_id: int
    contribution_amount: float = Field(..., gt=100)

class FundingPositionResponse(BaseModel):
    id: int
    loan_id: int
    lender_id: int
    lender_name: str
    contribution_amount: float
    share_pct: float
    funded_at: str
    status: str

class SyndicateSummaryResponse(BaseModel):
    loan_id: int
    requested_amount: float
    funded_amount: float
    remaining_amount: float
    funding_status: str
    positions: List[FundingPositionResponse]
    lender_concentration_index: float  # Herfindahl-Hirschman concentration (0 to 1)

# --- Repayment Schemas ---
class RepaymentScheduleItem(BaseModel):
    id: Optional[int] = None
    payment_number: int
    due_date: str
    scheduled_principal: float
    scheduled_interest: float
    scheduled_total: float
    remaining_balance: float
    status: str

class RepaymentExecutionRequest(BaseModel):
    amount_paid: float = Field(..., gt=0)
    allocation_policy: str = "PRO_RATA" # PRO_RATA, LARGEST_CONTRIBUTION_FIRST, EARLIEST_FUNDING_FIRST
    schedule_id: Optional[int] = None

class RepaymentAllocationBreakdown(BaseModel):
    lender_id: int
    lender_name: str
    share_pct: float
    principal_payout: float
    interest_payout: float
    total_payout: float

class RepaymentTransactionResponse(BaseModel):
    id: int
    loan_id: int
    schedule_id: Optional[int]
    payment_date: str
    amount_paid: float
    principal_allocated: float
    interest_allocated: float
    allocation_policy: str
    allocations: List[RepaymentAllocationBreakdown]

# --- What-If Simulation Schemas ---
class SimulationRequest(BaseModel):
    loan_id: Optional[int] = None
    credit_score: int = Field(..., ge=300, le=850)
    annual_income: float = Field(..., gt=0)
    loan_amount: float = Field(..., gt=0)
    dti_ratio: float = Field(..., ge=0.01, le=2.0)
    loan_term: int = Field(..., ge=3, le=60)
    months_employed: int = Field(..., ge=0)
    has_cosigner: int = Field(0, ge=0, le=1)

class SimulationResponse(BaseModel):
    baseline_pd: float
    baseline_risk_score: int
    baseline_risk_level: str
    scenario_pd: float
    scenario_risk_score: int
    scenario_risk_level: str
    pd_delta_pct_points: float
    score_delta: int
    key_sensitivities: List[Dict[str, Any]]
    disclaimer: str

# --- Authentication & User Schemas ---
class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: str

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400
    user: UserResponse

# --- Custom Domain & Institutional Configuration Schemas ---
class DomainConfigRequest(BaseModel):
    domain: str = Field(..., min_length=3, max_length=253)
    ssl_enabled: bool = True
    custom_cname: Optional[str] = None

class DomainConfigResponse(BaseModel):
    configured_domain: str
    ssl_status: str
    cname_target: str
    is_active: bool
    dns_records: List[Dict[str, str]]

# --- Legal & Compliance Schemas ---
class LegalDocumentResponse(BaseModel):
    title: str
    version: str
    effective_date: str
    jurisdiction: str
    sections: List[Dict[str, str]]

# --- Borrower Application & Zero-Trust Verification Schemas ---
class BorrowerApplicationRequest(BaseModel):
    full_name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=10)
    city: str = "Delhi"
    annual_income: float = Field(..., gt=0)
    loan_amount: float = Field(..., gt=1000)
    loan_term: int = Field(..., ge=1, le=60)
    interest_rate: float = Field(14.5, ge=1.0, le=48.0)
    loan_purpose: str = "Working Capital"
    unbanked_reason: str = "Lack of registered property collateral for commercial bank loan"
    has_cosigner: int = 0
    enach_mandate_consent: bool = True
    terms_agreed: bool = True

# --- Negotiation Hall Schemas ---
class NegotiationOfferRequest(BaseModel):
    loan_id: int
    lender_id: Optional[int] = 1
    proposed_principal: float = Field(..., gt=0)
    proposed_rate: float = Field(..., ge=1.0, le=48.0)
    proposed_term: int = Field(..., ge=1, le=60)
    sender_role: str = "lender" # lender or borrower
    sender_name: str = "Apex Credit Partners"
    message: str = "Counter-offer submitted."

# --- Mock Lender Creator Schemas ---
class MockLenderCreateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    capital_pool: float = Field(..., gt=1000)
    institution_type: str = "Private Individual"
    risk_tolerance: str = "BALANCED"
