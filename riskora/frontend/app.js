/**
 * RISKORA - National Digital Micro-Lending Portal Frontend Application
 * Official Banking / Regulatory Sandbox Standard (NIC / RBI Standard)
 */

const state = {
  currentTab: 'tab-gateway',
  currentPersona: 'borrower',
  loans: [],
  lenders: [],
  activeLenderId: 1,
  activeLoanId: null,
  currentNegotiation: null,
  currentOraAudit: null,
  myApplications: []
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  await loadLenders();
  await refreshLoansCatalog();
  await loadDomainInfo();
  renderBorrowerTracking();
}

// --- Persona Switcher ---
function switchPersona(persona) {
  state.currentPersona = persona;
  const btnBorrower = document.getElementById('personaBtnBorrower');
  const btnLender = document.getElementById('personaBtnLender');

  if (persona === 'borrower') {
    if (btnBorrower) btnBorrower.classList.add('active');
    if (btnLender) btnLender.classList.remove('active');
    switchTab('tab-borrower');
  } else {
    if (btnLender) btnLender.classList.add('active');
    if (btnBorrower) btnBorrower.classList.remove('active');
    switchTab('tab-lender');
  }
}

// --- Navigation Tabs ---
function switchTab(tabId) {
  state.currentTab = tabId;

  // Toggle tab panes
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.remove('active');
  });
  const targetPane = document.getElementById(tabId);
  if (targetPane) targetPane.classList.add('active');

  // Toggle nav links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('active');
    if (link.getAttribute('data-tab') === tabId) {
      link.classList.add('active');
    }
  });

  // Sync persona button highlights
  const btnBorrower = document.getElementById('personaBtnBorrower');
  const btnLender = document.getElementById('personaBtnLender');
  if (tabId === 'tab-borrower') {
    if (btnBorrower) btnBorrower.classList.add('active');
    if (btnLender) btnLender.classList.remove('active');
  } else if (tabId === 'tab-lender') {
    if (btnLender) btnLender.classList.add('active');
    if (btnBorrower) btnBorrower.classList.remove('active');
  }
}

// --- Dynamic EMI Math ---
function calculateEMI(principal, annualRate, termMonths) {
  if (!principal || !termMonths || principal <= 0 || termMonths <= 0) return 0;
  if (!annualRate || annualRate <= 0) return Math.round(principal / termMonths);
  const monthlyRate = (annualRate / 100.0) / 12.0;
  const factor = Math.pow(1 + monthlyRate, termMonths);
  const emi = principal * monthlyRate * (factor / (factor - 1));
  return Math.round(emi);
}

function recalcLiveEmi() {
  const p = parseFloat(document.getElementById('negInputPrincipal')?.value) || 50000;
  const r = parseFloat(document.getElementById('negInputRate')?.value) || 15;
  const n = parseInt(document.getElementById('negInputTerm')?.value) || 12;
  const emi = calculateEMI(p, r, n);
  const display = document.getElementById('negCalculatedEmiDisplay');
  if (display) {
    display.textContent = '₹' + emi.toLocaleString('en-IN');
  }
}

// --- Lenders Management ---
async function loadLenders() {
  try {
    const res = await fetch('/api/lenders');
    if (res.ok) {
      state.lenders = await res.json();
      populateLenderDropdown();
    }
  } catch (err) {
    console.warn('Failed to load lenders:', err);
  }
}

function populateLenderDropdown() {
  const sel = document.getElementById('activeLenderSelect');
  if (!sel) return;
  sel.innerHTML = '';
  state.lenders.forEach(l => {
    const opt = document.createElement('option');
    opt.value = l.id;
    opt.textContent = `${l.name} (${l.institution_type})`;
    sel.appendChild(opt);
  });
  if (state.lenders.length > 0) {
    sel.value = state.activeLenderId;
    updateActiveLenderPoolDisplay();
  }
}

function onLenderChanged() {
  const sel = document.getElementById('activeLenderSelect');
  if (!sel) return;
  state.activeLenderId = parseInt(sel.value) || 1;
  updateActiveLenderPoolDisplay();
}

function updateActiveLenderPoolDisplay() {
  const lender = state.lenders.find(l => l.id === state.activeLenderId);
  const poolSpan = document.getElementById('activeLenderPool');
  if (poolSpan && lender) {
    poolSpan.textContent = '₹' + (lender.available_balance || lender.total_committed || 250000).toLocaleString('en-IN');
  }
}

// --- Mock Lender Creator ---
function openMockLenderModal() {
  openModal('mockLenderModal');
}

async function createMockLender() {
  const name = document.getElementById('mockLenderName')?.value.trim();
  const capital = parseFloat(document.getElementById('mockLenderCapital')?.value) || 100000;
  const instType = document.getElementById('mockLenderType')?.value || 'Private Individual';

  if (!name) {
    alert('Please provide a lender name.');
    return;
  }

  try {
    const res = await fetch('/api/lenders/mock', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        capital_pool: capital,
        institution_type: instType,
        risk_tolerance: 'BALANCED'
      })
    });

    if (res.ok) {
      const newLender = await res.json();
      state.lenders.push(newLender);
      state.activeLenderId = newLender.id;
      populateLenderDropdown();
      closeModal('mockLenderModal');
      alert(`Lender instance '${name}' created successfully with ₹${capital.toLocaleString('en-IN')} capital pool.`);
    } else {
      const err = await res.json();
      alert('Error creating lender: ' + (err.detail || 'Server error'));
    }
  } catch (e) {
    alert('Connection failure: ' + e.message);
  }
}

// --- Borrower Application Submission ---
async function submitBorrowerApplication() {
  const fullName = document.getElementById('borrowerFullName')?.value.trim();
  const phone = document.getElementById('borrowerPhone')?.value.trim();
  const city = document.getElementById('borrowerCity')?.value.trim();
  const annualIncome = parseFloat(document.getElementById('borrowerAnnualIncome')?.value) || 360000;
  const loanAmount = parseFloat(document.getElementById('borrowerLoanAmount')?.value) || 45000;
  const loanTerm = parseInt(document.getElementById('borrowerLoanTerm')?.value) || 12;
  const interestRate = parseFloat(document.getElementById('borrowerInterestRate')?.value) || 14.0;
  const loanPurpose = document.getElementById('borrowerLoanPurpose')?.value || 'Working Capital';
  const unbankedReason = document.getElementById('borrowerUnbankedReason')?.value.trim();
  const termsAgreed = document.getElementById('borrowerTermsConsent')?.checked;
  const enachConsent = document.getElementById('borrowerEnachConsent')?.checked;

  if (!termsAgreed || !enachConsent) {
    alert('You must accept the terms of service and authorize the eNACH auto-debit mandate before submitting.');
    return;
  }

  const payload = {
    full_name: fullName,
    phone: phone,
    city: city,
    annual_income: annualIncome,
    loan_amount: loanAmount,
    loan_term: loanTerm,
    interest_rate: interestRate,
    loan_purpose: loanPurpose,
    unbanked_reason: unbankedReason,
    has_cosigner: 0,
    enach_mandate_consent: true,
    terms_agreed: true
  };

  try {
    const res = await fetch('/api/borrowers/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      state.myApplications.unshift({
        loan_id: data.loan_id,
        loan_code: data.loan_code,
        borrower_name: fullName,
        loan_amount: loanAmount,
        loan_term: loanTerm,
        interest_rate: interestRate,
        unbanked_reason: unbankedReason,
        status: data.status,
        mandate_registered: true
      });

      renderBorrowerTracking();
      alert(`Loan Application ${data.loan_code} successfully posted to the marketplace with verified eNACH mandate.`);
      await refreshLoansCatalog();
    } else {
      const err = await res.json();
      alert('Application failed: ' + (err.detail || 'Validation error'));
    }
  } catch (e) {
    alert('Network error: ' + e.message);
  }
}

function resetBorrowerForm() {
  const form = document.getElementById('borrowerApplicationForm');
  if (form) form.reset();
}

function renderBorrowerTracking() {
  const container = document.getElementById('borrowerTrackingList');
  if (!container) return;

  if (state.myApplications.length === 0) {
    // Add default initial tracked loan
    state.myApplications = [{
      loan_id: 1,
      loan_code: 'LN-2026-001',
      borrower_name: 'Aarav Sharma',
      loan_amount: 50000,
      loan_term: 12,
      interest_rate: 15.0,
      unbanked_reason: 'Lack of immovable real-estate collateral; commercial bank branch rejected ticket size under 1 Lakh.',
      status: 'APPLIED',
      mandate_registered: true
    }];
  }

  container.innerHTML = '';
  state.myApplications.forEach(app => {
    const card = document.createElement('div');
    card.className = 'borrower-tracker-card';
    card.innerHTML = `
      <div>
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
          <strong style="font-size: 14px; color: var(--navy-primary);">${app.loan_code} - ₹${app.loan_amount.toLocaleString('en-IN')}</strong>
          <span class="verification-tag tag-saffron">${app.status}</span>
          <span class="verification-tag tag-verified">eNACH AUTHORIZED</span>
        </div>
        <div style="font-size: 12px; color: var(--text-secondary);">
          Tenor: ${app.loan_term} Months | Base Rate: ${app.interest_rate}% | Monthly Inflow Verification: Cleared
        </div>
        <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 4px;">
          Stated Need: ${app.unbanked_reason}
        </div>
      </div>
      <div>
        <button class="btn-secondary" style="padding: 6px 12px; font-size: 11.5px;" onclick="openNegotiationModal(${app.loan_id})">
          View Counter-Offers
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

// --- Loans Catalog (Lender Marketplace) ---
async function refreshLoansCatalog() {
  try {
    const res = await fetch('/api/loans?limit=50');
    if (res.ok) {
      const data = await res.json();
      state.loans = data.loans || [];
      renderLoansCatalog(state.loans);
    }
  } catch (err) {
    console.warn('Failed to load loans catalog:', err);
  }
}

function filterLoansCatalog() {
  const q = document.getElementById('catalogSearchInput')?.value.toLowerCase().trim() || '';
  const risk = document.getElementById('catalogRiskFilter')?.value || '';
  const stat = document.getElementById('catalogStatusFilter')?.value || '';

  const filtered = state.loans.filter(l => {
    const b = l.borrower || {};
    const matchesQuery = !q ||
      b.full_name?.toLowerCase().includes(q) ||
      b.city?.toLowerCase().includes(q) ||
      l.loan_code?.toLowerCase().includes(q) ||
      l.loan_purpose?.toLowerCase().includes(q);

    const matchesRisk = !risk || (l.risk_assessment?.risk_level === risk);
    const matchesStatus = !stat || (l.status === stat);

    return matchesQuery && matchesRisk && matchesStatus;
  });

  renderLoansCatalog(filtered);
}

function renderLoansCatalog(loans) {
  const container = document.getElementById('borrowerCardsContainer');
  if (!container) return;
  container.innerHTML = '';

  if (loans.length === 0) {
    container.innerHTML = '<div style="padding: 24px; text-align: center; color: var(--text-muted);">No verified borrowers found matching filters.</div>';
    return;
  }

  loans.forEach(loan => {
    const b = loan.borrower || {};
    const risk = loan.risk_assessment || {};
    const riskLevel = risk.risk_level || 'LOW';
    const riskScore = risk.risk_score || 720;
    const monthlyIncome = b.bank_verified_monthly_income || (b.annual_income ? b.annual_income / 12 : 35000);
    const unbankedReason = b.unbanked_reason || 'Lack of collateral assets for traditional banking';

    const card = document.createElement('div');
    card.className = 'borrower-card';
    card.innerHTML = `
      <div>
        <div class="borrower-card-header">
          <div>
            <h4 class="borrower-name">${b.full_name || 'Borrower'}</h4>
            <div class="borrower-meta">${b.city || 'India'} | ID: ${loan.loan_code}</div>
          </div>
          <span class="verification-tag ${riskLevel === 'LOW' ? 'tag-verified' : 'tag-saffron'}">
            ${riskLevel} RISK (${risk.probability_of_default ? (risk.probability_of_default * 100).toFixed(1) + '%' : '18%'} PD)
          </span>
        </div>

        <!-- Unbanked Reason Pill -->
        <div class="unbanked-reason-pill">
          <strong>Reason for Micro-Credit:</strong>
          ${unbankedReason}
        </div>

        <!-- Zero-Trust Verification Seals -->
        <div class="verification-seals-row">
          <span class="seal-badge seal-green">✔ Aadhaar Biometrics</span>
          <span class="seal-badge seal-green">✔ AA Bank Inflow (₹${Math.round(monthlyIncome).toLocaleString('en-IN')}/mo)</span>
          <span class="seal-badge seal-blue">✔ eNACH Mandate</span>
        </div>

        <!-- Metrics Strip -->
        <div class="borrower-metrics-strip">
          <div>
            <div class="b-metric-val">₹${loan.loan_amount.toLocaleString('en-IN')}</div>
            <div class="b-metric-lbl">Requested</div>
          </div>
          <div>
            <div class="b-metric-val">${loan.loan_term} Mo</div>
            <div class="b-metric-lbl">Tenor</div>
          </div>
          <div>
            <div class="b-metric-val">${loan.interest_rate}%</div>
            <div class="b-metric-lbl">Base Rate</div>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="borrower-card-actions">
        <button class="btn-ora" onclick="openOraModal(${loan.id})">
          RUN ORA RISK ANALYSIS
        </button>
        <button class="btn-secondary" style="font-size: 12px; padding: 6px 10px;" onclick="openNegotiationModal(${loan.id})">
          Single Lender: Negotiate Terms
        </button>
        <button class="btn-primary" style="font-size: 12px; padding: 6px 10px;" onclick="openSyndicateModal(${loan.id})">
          Multi-Lender: Syndicate Funding
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

// --- Case A: Single Lender Negotiation Hall ---
async function openNegotiationModal(loanId) {
  state.activeLoanId = loanId;
  const modal = document.getElementById('negotiationModal');
  if (!modal) return;

  try {
    const res = await fetch(`/api/negotiations/${loanId}`);
    if (res.ok) {
      state.currentNegotiation = await res.json();
    }
    const loanRes = await fetch(`/api/loans/${loanId}`);
    const loanData = loanRes.ok ? await loanRes.json() : null;

    populateNegotiationUI(loanData);
    openModal('negotiationModal');
  } catch (e) {
    alert('Failed to load negotiation session: ' + e.message);
  }
}

function populateNegotiationUI(loanData) {
  const neg = state.currentNegotiation || {};
  const bName = loanData?.borrower?.full_name || 'Borrower';
  const principal = neg.current_principal || loanData?.loan_amount || 50000;
  const rate = neg.current_interest_rate || loanData?.interest_rate || 15.0;
  const term = neg.current_term || loanData?.loan_term || 12;

  document.getElementById('negModalTitle').textContent = `Single Lender Negotiation Hall: Loan ${loanData?.loan_code || ''}`;
  document.getElementById('negBorrowerName').textContent = bName;
  document.getElementById('negActivePrincipal').textContent = '₹' + principal.toLocaleString('en-IN');
  document.getElementById('negActiveRate').textContent = rate + '%';
  document.getElementById('negActiveTerm').textContent = term + ' Months';

  const emi = calculateEMI(principal, rate, term);
  document.getElementById('negCalculatedEmiDisplay').textContent = '₹' + emi.toLocaleString('en-IN');

  const statusSpan = document.getElementById('negContractStatus');
  if (statusSpan) {
    if (neg.status === 'ACCEPTED_AND_LOCKED') {
      statusSpan.className = 'verification-tag tag-verified';
      statusSpan.textContent = 'TERMS LOCKED & ACTIVE';
      document.getElementById('btnAcceptLockTerms').disabled = true;
    } else {
      statusSpan.className = 'verification-tag tag-saffron';
      statusSpan.textContent = 'OPEN NEGOTIATION';
      document.getElementById('btnAcceptLockTerms').disabled = false;
    }
  }

  // Pre-fill counter offer inputs
  document.getElementById('negInputPrincipal').value = principal;
  document.getElementById('negInputRate').value = rate;
  document.getElementById('negInputTerm').value = term;
  document.getElementById('negInputMessage').value = '';

  // Render chat history
  const chatContainer = document.getElementById('negChatContainer');
  chatContainer.innerHTML = '';
  const history = neg.history || [];

  history.forEach(item => {
    const bubble = document.createElement('div');
    const isLender = item.sender === 'lender';
    const isSystem = item.sender === 'system';

    bubble.className = `chat-bubble ${isSystem ? 'system' : isLender ? 'lender' : 'borrower'}`;
    bubble.innerHTML = `
      <div class="chat-author">
        <span>${item.sender_name || (isLender ? 'Lender' : isSystem ? 'RiskOra Protocol' : 'Borrower')}</span>
        <span>${item.timestamp ? item.timestamp.substring(11, 16) : ''}</span>
      </div>
      <div>${item.message}</div>
      ${item.rate ? `
        <div style="font-weight: 700; margin-top: 4px; font-size: 11.5px;">
          Proposed: ₹${(item.principal || principal).toLocaleString('en-IN')} @ ${item.rate}% for ${item.term} Mo (EMI: ₹${(item.emi || calculateEMI(item.principal, item.rate, item.term)).toLocaleString('en-IN')})
        </div>
      ` : ''}
    `;
    chatContainer.appendChild(bubble);
  });
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function submitCounterOffer() {
  const p = parseFloat(document.getElementById('negInputPrincipal')?.value);
  const r = parseFloat(document.getElementById('negInputRate')?.value);
  const n = parseInt(document.getElementById('negInputTerm')?.value);
  const msg = document.getElementById('negInputMessage')?.value.trim() || 'Counter-offer submitted.';

  const activeLender = state.lenders.find(l => l.id === state.activeLenderId);
  const lenderName = activeLender ? activeLender.name : 'Apex Credit Partners';

  const payload = {
    loan_id: state.activeLoanId,
    lender_id: state.activeLenderId,
    proposed_principal: p,
    proposed_rate: r,
    proposed_term: n,
    sender_role: 'lender',
    sender_name: lenderName,
    message: msg
  };

  try {
    const res = await fetch('/api/negotiations/offer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      await openNegotiationModal(state.activeLoanId);
    } else {
      const err = await res.json();
      alert('Error submitting counter-offer: ' + (err.detail || 'Server error'));
    }
  } catch (e) {
    alert('Network error: ' + e.message);
  }
}

async function acceptAndLockNegotiation() {
  if (!confirm('Are you sure you want to accept and lock these terms? The loan contract will be finalized and registered under the eNACH mandate.')) return;

  try {
    const res = await fetch(`/api/negotiations/accept/${state.activeLoanId}`, {
      method: 'POST'
    });

    if (res.ok) {
      const data = await res.json();
      alert(data.message || 'Terms locked and contract frozen.');
      await openNegotiationModal(state.activeLoanId);
      await refreshLoansCatalog();
    } else {
      const err = await res.json();
      alert('Error accepting terms: ' + (err.detail || 'Server error'));
    }
  } catch (e) {
    alert('Connection failure: ' + e.message);
  }
}

// --- Case B: Multi-Lender Fractional Ledger ---
async function openSyndicateModal(loanId) {
  state.activeLoanId = loanId;
  try {
    const res = await fetch(`/api/funding/syndicate/${loanId}`);
    if (res.ok) {
      const syn = await res.json();
      populateSyndicateUI(syn);
      openModal('syndicateModal');
    }
  } catch (e) {
    alert('Failed to load syndicate data: ' + e.message);
  }
}

function populateSyndicateUI(syn) {
  document.getElementById('synModalTitle').textContent = `The Fractional Ledger: Loan #${syn.loan_id} Syndication`;
  document.getElementById('synTotalRequested').textContent = '₹' + syn.requested_amount.toLocaleString('en-IN');
  document.getElementById('synTotalFunded').textContent = '₹' + syn.funded_amount.toLocaleString('en-IN');
  document.getElementById('synRemaining').textContent = '₹' + syn.remaining_amount.toLocaleString('en-IN');

  const pct = Math.min(100, Math.round((syn.funded_amount / Math.max(syn.requested_amount, 1)) * 100));
  document.getElementById('synProgressPct').textContent = pct + '%';
  document.getElementById('synProgressFill').style.width = pct + '%';

  const tbody = document.getElementById('synPositionsBody');
  tbody.innerHTML = '';

  const positions = syn.positions || [];
  if (positions.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No fractional positions pledged yet. Be the first to deploy capital.</td></tr>';
  } else {
    positions.forEach(p => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${p.lender_name}</strong></td>
        <td>₹${p.contribution_amount.toLocaleString('en-IN')}</td>
        <td>${p.share_pct.toFixed(1)}%</td>
        <td><span class="verification-tag tag-verified">${p.status}</span></td>
      `;
      tbody.appendChild(tr);
    });
  }
}

async function pledgeFractionalFunding() {
  const amt = parseFloat(document.getElementById('synPledgeAmount')?.value);
  if (!amt || amt <= 0) {
    alert('Please enter a valid pledge amount.');
    return;
  }

  try {
    const res = await fetch(`/api/funding/pledge/${state.activeLoanId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lender_id: state.activeLenderId,
        contribution_amount: amt
      })
    });

    if (res.ok) {
      document.getElementById('synPledgeAmount').value = '';
      await openSyndicateModal(state.activeLoanId);
      await refreshLoansCatalog();
    } else {
      const err = await res.json();
      alert('Pledge failed: ' + (err.detail || 'Allocation ceiling reached'));
    }
  } catch (e) {
    alert('Network error: ' + e.message);
  }
}

async function executeLoanRepayment() {
  const policy = document.getElementById('synRoutingPolicy')?.value || 'PRO_RATA';
  const emiAmount = 4500; // Standard simulated installment

  try {
    const res = await fetch(`/api/repayments/execute/${state.activeLoanId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount_paid: emiAmount,
        allocation_policy: policy
      })
    });

    if (res.ok) {
      const data = await res.json();
      const breakdownText = data.allocations?.map(a => `${a.lender_name}: ₹${a.total_paid.toLocaleString('en-IN')}`).join(' | ') || 'Allocated to participating lenders.';

      showRepaymentToast(
        'REPAYMENT ALLOCATED WITHOUT PENNY LEAKAGE',
        `₹${emiAmount.toLocaleString('en-IN')} received via automated eNACH mandate. Distributed via ${policy}: ${breakdownText}`
      );
      await openSyndicateModal(state.activeLoanId);
    } else {
      const err = await res.json();
      alert('Repayment simulation error: ' + (err.detail || 'Execution failure'));
    }
  } catch (e) {
    alert('Network error: ' + e.message);
  }
}

function downloadPerformanceReport() {
  if (!state.activeLoanId) return;
  window.open(`/api/reports/${state.activeLoanId}/performance`, '_blank');
}

// --- ORA Explainable Risk Agent Engine ---
async function openOraModal(loanId) {
  state.activeLoanId = loanId;
  try {
    const res = await fetch(`/api/risk/ora-analyze/${loanId}`, { method: 'POST' });
    if (res.ok) {
      const audit = await res.json();
      state.currentOraAudit = audit;
      populateOraUI(audit);
      openModal('oraModal');
    } else {
      const err = await res.json();
      alert('ORA Analysis error: ' + (err.detail || 'Inference failure'));
    }
  } catch (e) {
    alert('Connection error: ' + e.message);
  }
}

function populateOraUI(audit) {
  document.getElementById('oraModalTitle').textContent = `ORA Explainable Risk Agent: Loan ${audit.loan_code} (${audit.borrower_name})`;
  document.getElementById('oraScoreValue').textContent = audit.ora_score;

  // Position needle between 300 and 900
  const needlePct = Math.max(0, Math.min(100, ((audit.ora_score - 300) / 600) * 100));
  document.getElementById('oraMeterNeedle').style.left = needlePct + '%';

  const gradeBadge = document.getElementById('oraRiskGradeBadge');
  gradeBadge.textContent = `GRADE: ${audit.risk_grade} RISK (${audit.probability_pct}% PD)`;
  gradeBadge.className = audit.risk_grade === 'LOW' ? 'verification-tag tag-verified' : 'verification-tag tag-saffron';

  document.getElementById('oraVerdictText').textContent = audit.verdict;

  // Vectors
  const vectorTbody = document.getElementById('oraVectorTableBody');
  vectorTbody.innerHTML = '';
  (audit.vector_analysis || []).forEach(v => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${v.factor}</strong></td>
      <td><span class="verification-tag tag-verified">${v.status}</span></td>
      <td>${v.detail}</td>
    `;
    vectorTbody.appendChild(tr);
  });

  // Evidence List
  const evidenceList = document.getElementById('oraEvidenceList');
  evidenceList.innerHTML = '';
  (audit.evidence_foundation || []).forEach(ev => {
    const d = document.createElement('div');
    d.style.cssText = 'padding: 4px 0; font-size: 12px; color: var(--text-primary); border-bottom: 1px solid var(--border-light);';
    d.innerHTML = `&bull; ${ev}`;
    evidenceList.appendChild(d);
  });

  document.getElementById('oraCryptoHashText').textContent = audit.cryptographic_hash;
}

function copyOraHash() {
  const hash = document.getElementById('oraCryptoHashText')?.textContent;
  if (hash) {
    navigator.clipboard.writeText(hash).then(() => {
      alert('Cryptographic proof hash copied to clipboard!');
    });
  }
}

function downloadOraCertificate() {
  if (!state.activeLoanId) return;
  window.open(`/api/reports/${state.activeLoanId}/ora-certificate`, '_blank');
}

// --- Browser Notification Toast ---
function showRepaymentToast(title, body) {
  const toast = document.getElementById('repaymentToast');
  const toastBody = document.getElementById('repaymentToastBody');
  if (!toast) return;

  toast.querySelector('.toast-title').textContent = title;
  if (toastBody) toastBody.textContent = body;

  toast.style.display = 'block';
  setTimeout(() => {
    toast.style.display = 'none';
  }, 6000);
}

// --- Modals Base ---
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('active');
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('active');
}

// --- Legal & Domain Info ---
async function loadDomainInfo() {
  try {
    const res = await fetch('/api/config/domain');
    if (res.ok) {
      const data = await res.json();
      const badge = document.getElementById('headerDomainText');
      if (badge) badge.textContent = data.configured_domain;
      const modalSpan = document.getElementById('modalDomainName');
      if (modalSpan) modalSpan.textContent = data.configured_domain;
    }
  } catch (err) {
    console.warn('Domain info error:', err);
  }
}

function openDomainModal() {
  openModal('domainModal');
}

async function updateDomain() {
  const domain = document.getElementById('inputDomainName')?.value.trim();
  if (!domain) return;
  try {
    const res = await fetch('/api/config/domain', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain: domain })
    });
    if (res.ok) {
      alert('Custom domain registered successfully.');
      closeModal('domainModal');
      await loadDomainInfo();
    }
  } catch (e) {
    alert('Error updating domain: ' + e.message);
  }
}

function openLoginModal() {
  openModal('loginModal');
}

async function loginUser() {
  const u = document.getElementById('loginUsername')?.value.trim();
  const p = document.getElementById('loginPassword')?.value;
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: u, password: p })
    });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('riskora_token', data.access_token);
      alert('Authentication successful as ' + data.user.role);
      closeModal('loginModal');
      const authBtn = document.getElementById('loginBtn');
      if (authBtn) authBtn.textContent = 'Authenticated: ' + data.user.username;
    } else {
      alert('Authentication failed.');
    }
  } catch (e) {
    alert('Connection failure: ' + e.message);
  }
}

async function openPrivacyModal() {
  openModal('privacyModal');
  try {
    const res = await fetch('/api/legal/privacy');
    if (res.ok) {
      const doc = await res.json();
      const container = document.getElementById('privacyContent');
      container.innerHTML = `
        <h4 style="margin-bottom: 8px; color: var(--navy-primary);">${doc.title} (Ver ${doc.version})</h4>
        <div style="font-size: 11.5px; color: var(--text-muted); margin-bottom: 14px;">Jurisdiction: ${doc.jurisdiction}</div>
      `;
      doc.sections.forEach(s => {
        container.innerHTML += `
          <div style="margin-bottom: 12px;">
            <strong>${s.heading}</strong>
            <p style="margin-top: 2px;">${s.body}</p>
          </div>
        `;
      });
    }
  } catch (e) {
    console.warn(e);
  }
}

async function openTermsModal() {
  openModal('termsModal');
  try {
    const res = await fetch('/api/legal/terms');
    if (res.ok) {
      const doc = await res.json();
      const container = document.getElementById('termsContent');
      container.innerHTML = `
        <h4 style="margin-bottom: 8px; color: var(--navy-primary);">${doc.title} (Ver ${doc.version})</h4>
        <div style="font-size: 11.5px; color: var(--text-muted); margin-bottom: 14px;">Jurisdiction: ${doc.jurisdiction}</div>
      `;
      doc.sections.forEach(s => {
        container.innerHTML += `
          <div style="margin-bottom: 12px;">
            <strong>${s.heading}</strong>
            <p style="margin-top: 2px;">${s.body}</p>
          </div>
        `;
      });
    }
  } catch (e) {
    console.warn(e);
  }
}

async function uploadDatasetFile() {
  const fileInput = document.getElementById('datasetUploadInput');
  const statusDiv = document.getElementById('datasetUploadStatus');
  if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
    alert('Please select a CSV file.');
    return;
  }
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);

  statusDiv.textContent = 'Processing dataset and evaluating ML default probabilities...';
  try {
    const res = await fetch('/api/datasets/upload', {
      method: 'POST',
      body: formData
    });
    if (res.ok) {
      const data = await res.json();
      statusDiv.textContent = data.message;
      statusDiv.style.color = 'var(--tricolor-green)';
    } else {
      const err = await res.json();
      statusDiv.textContent = 'Upload error: ' + (err.detail || 'CSV format issue');
      statusDiv.style.color = 'var(--risk-alert-red)';
    }
  } catch (e) {
    statusDiv.textContent = 'Network error: ' + e.message;
  }
}
