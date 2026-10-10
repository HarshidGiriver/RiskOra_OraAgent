"""
RISKORA - Security, Cryptography & Auth Test Suite
Validates PBKDF2 hashing, JWT signing, rate limiting, XSS sanitization,
authentication endpoints, and institutional security headers.
"""

import pytest
import time
from fastapi.testclient import TestClient
from riskora.backend.main import app
from riskora.backend.database import reset_db, init_db
from riskora.backend.security import (
    hash_password, verify_password,
    create_access_token, decode_access_token,
    sanitize_input, RateLimiter
)

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    reset_db()

def test_pbkdf2_password_hashing():
    pwd = "SecureInstitutionalPassword@2026"
    salt, hash_val = hash_password(pwd)
    
    # Assert proper output formats
    assert len(salt) == 64  # 32 bytes hex
    assert len(hash_val) == 64 # SHA-256 hex
    
    # Assert verification succeeds with correct password
    assert verify_password(pwd, salt, hash_val) is True
    
    # Assert verification fails with incorrect password
    assert verify_password("WrongPassword@123", salt, hash_val) is False
    
    # Assert salt uniqueness (two hashes of same password produce different salts/hashes)
    salt2, hash_val2 = hash_password(pwd)
    assert salt != salt2
    assert hash_val != hash_val2

def test_jwt_token_creation_and_validation():
    payload = {"sub": "1", "username": "admin", "role": "admin"}
    token = create_access_token(payload, expires_delta=3600)
    
    assert isinstance(token, str)
    assert len(token.split('.')) == 3
    
    claims = decode_access_token(token)
    assert claims["sub"] == "1"
    assert claims["username"] == "admin"
    assert claims["role"] == "admin"
    assert "exp" in claims
    assert "iat" in claims

def test_jwt_tampering_rejection():
    payload = {"sub": "2", "username": "underwriter", "role": "underwriter"}
    token = create_access_token(payload, expires_delta=3600)
    
    # Tamper with payload
    parts = token.split('.')
    tampered_token = f"{parts[0]}.eyJzdWIiOiAiMiIsICJyb2xlIjogImFkbWluIn0.{parts[2]}"
    
    with pytest.raises(ValueError, match="Invalid cryptographic signature"):
        decode_access_token(tampered_token)

def test_jwt_expiration_rejection():
    payload = {"sub": "3", "username": "lender", "role": "lender"}
    # Token expired 10 seconds ago
    token = create_access_token(payload, expires_delta=-10)
    
    with pytest.raises(ValueError, match="Token has expired"):
        decode_access_token(token)

def test_xss_input_sanitization():
    xss_payload = "<script>alert('xss')</script>Hello"
    sanitized = sanitize_input(xss_payload)
    assert "<script>" not in sanitized
    assert "&lt;script&gt;" in sanitized
    
    js_link = "javascript:alert(1)"
    sanitized_link = sanitize_input(js_link)
    assert "javascript:" not in sanitized_link.lower()
    
    # Test nested dict sanitization
    nested = {"name": "<b>John</b>", "notes": ["<img src=x onerror=alert(1)>"]}
    clean_nested = sanitize_input(nested)
    assert "<b>" not in clean_nested["name"]
    assert "<img" not in clean_nested["notes"][0]

def test_sliding_window_rate_limiter():
    limiter = RateLimiter(max_requests=5, window_seconds=2)
    client_ip = "192.168.1.100"
    
    # First 5 requests must pass
    for _ in range(5):
        assert limiter.is_allowed(client_ip) is True
        
    # 6th request must be rejected
    assert limiter.is_allowed(client_ip) is False
    
    # Different IP should still pass
    assert limiter.is_allowed("192.168.1.101") is True

def test_auth_login_success():
    res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "AdminPassword@2026"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"

def test_auth_login_invalid_credentials():
    res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "IncorrectPassword"
    })
    assert res.status_code == 401
    assert "Invalid username or password" in res.json()["detail"]

def test_auth_me_endpoint():
    # Login first
    login_res = client.post("/api/auth/login", json={
        "username": "underwriter",
        "password": "Underwriter@2026"
    })
    token = login_res.json()["access_token"]
    
    # Fetch profile with bearer token
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    profile = res.json()
    assert profile["username"] == "underwriter"
    assert profile["role"] == "underwriter"

def test_security_headers_injected():
    res = client.get("/api/health")
    assert res.status_code == 200
    
    headers = res.headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["x-xss-protection"] == "1; mode=block"
    assert "strict-transport-security" in headers
    assert "content-security-policy" in headers

def test_custom_domain_endpoints():
    res = client.get("/api/config/domain")
    assert res.status_code == 200
    data = res.json()
    assert "configured_domain" in data
    assert data["is_active"] is True
    
    update_res = client.post("/api/config/domain", json={
        "domain": "credit.riskora.institutional",
        "ssl_enabled": True
    })
    assert update_res.status_code == 200
    assert update_res.json()["configured_domain"] == "credit.riskora.institutional"

def test_legal_compliance_endpoints():
    privacy = client.get("/api/legal/privacy")
    assert privacy.status_code == 200
    assert "Privacy" in privacy.json()["title"]
    assert len(privacy.json()["sections"]) >= 3
    
    terms = client.get("/api/legal/terms")
    assert terms.status_code == 200
    assert "Terms" in terms.json()["title"]
    assert len(terms.json()["sections"]) >= 3
