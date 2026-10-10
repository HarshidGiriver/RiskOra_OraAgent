"""
RISKORA - Production Security, Cryptography & Rate Limiting Engine
Provides PBKDF2-HMAC-SHA256 salted password hashing, JWT token verification,
sliding-window rate limiting, XSS input sanitization, and security headers.
"""

import os
import time
import hmac
import hashlib
import json
import base64
import html
import re
from typing import Dict, Any, Tuple, Optional, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

# Secret configuration loaded from environment
SECRET_KEY = os.environ.get("RISKORA_SECRET_KEY", "riskora_prod_super_secret_signing_key_2026_secured")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 86400  # 24 Hours

# --- 1. Cryptographic Password Hashing (PBKDF2-HMAC-SHA256) ---
def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hashes a password with a 32-byte cryptographically secure random salt
    using 120,000 iterations of PBKDF2-HMAC-SHA256.
    Returns (salt_hex, hash_hex).
    """
    if salt is None:
        salt_bytes = os.urandom(32)
        salt_hex = salt_bytes.hex()
    else:
        salt_hex = salt
        salt_bytes = bytes.fromhex(salt_hex)

    derived = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        iterations=120000
    )
    return salt_hex, derived.hex()

def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    """Verifies a password against the stored salt and hash in constant time."""
    _, calculated_hash = hash_password(password, salt=salt_hex)
    return hmac.compare_digest(calculated_hash, hash_hex)

# --- 2. JSON Web Token (JWT) Implementation ---
def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(payload: Dict[str, Any], expires_delta: Optional[int] = None) -> str:
    """Generates a cryptographically signed HMAC-SHA256 JWT."""
    exp = int(time.time()) + (expires_delta or JWT_EXPIRATION_SECONDS)
    token_claims = payload.copy()
    token_claims["exp"] = exp
    token_claims["iat"] = int(time.time())

    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = _base64url_encode(json.dumps(token_claims).encode('utf-8'))

    signature_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    sig = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
    sig_b64 = _base64url_encode(sig)

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Dict[str, Any]:
    """Validates JWT signature and expiration. Raises ValueError if invalid."""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Malformed token structure.")

    header_b64, payload_b64, sig_b64 = parts
    signature_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
    actual_sig = _base64url_decode(sig_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid cryptographic signature.")

    claims = json.loads(_base64url_decode(payload_b64).decode('utf-8'))
    if claims.get("exp", 0) < int(time.time()):
        raise ValueError("Token has expired.")

    return claims

# --- 3. Input Sanitization & XSS Defense ---
def sanitize_input(value: Any) -> Any:
    """
    Sanitizes string input to prevent Cross-Site Scripting (XSS).
    Escapes HTML entities and neutralizes script injection patterns.
    """
    if isinstance(value, str):
        # Escape HTML entities
        escaped = html.escape(value.strip())
        # Neutralize common script or iframe payloads
        escaped = re.sub(r'javascript:', '', escaped, flags=re.IGNORECASE)
        escaped = re.sub(r'data:', '', escaped, flags=re.IGNORECASE)
        return escaped
    elif isinstance(value, dict):
        return {k: sanitize_input(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_input(v) for v in value]
    return value

# --- 4. Sliding-Window Rate Limiter ---
class RateLimiter:
    """In-memory rate limiter enforcing request thresholds per client IP."""
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Clean expired timestamps
        history = [ts for ts in self.requests.get(client_ip, []) if ts > cutoff]
        if len(history) >= self.max_requests:
            self.requests[client_ip] = history
            return False
            
        history.append(now)
        self.requests[client_ip] = history
        return True

global_rate_limiter = RateLimiter(max_requests=120, window_seconds=60)

# --- 5. Security Headers & Rate Limiting Middleware ---
class ProductionSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"

        # Apply rate limiting on API endpoints
        if request.url.path.startswith("/api/"):
            if not global_rate_limiter.is_allowed(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Maximum 120 requests per minute allowed."}
                )

        response: Response = await call_next(request)

        # Inject institutional security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy (allows required Google Fonts and Chart.js CDN, strictly no unsafe external script)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
        )

        return response
