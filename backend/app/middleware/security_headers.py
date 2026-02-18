"""
Revolution X - Security Headers Middleware
CSP, HSTS, and other security headers
"""
from fastapi import Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.logging import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.csp_policy = self._build_csp_policy()
    
    def _build_csp_policy(self) -> str:
        """Build Content Security Policy."""
        directives = {
            "default-src": ["'self'"],
            "script-src": [
                "'self'",
                "'unsafe-inline'",  # Required for some React features
                "'unsafe-eval'",    # Required for WebAssembly
                "https://cdn.jsdelivr.net",
                "https://unpkg.com",
            ],
            "style-src": [
                "'self'",
                "'unsafe-inline'",
                "https://fonts.googleapis.com",
                "https://cdn.jsdelivr.net",
            ],
            "img-src": [
                "'self'",
                "data:",
                "blob:",
                "https://api.revolutionx.com",
                "https://cdn.revolutionx.com",
            ],
            "font-src": [
                "'self'",
                "https://fonts.gstatic.com",
                "data:",
            ],
            "connect-src": [
                "'self'",
                "wss://api.revolutionx.com",
                "https://api.revolutionx.com",
            ],
            "media-src": ["'self'"],
            "object-src": ["'none'"],
            "frame-ancestors": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "upgrade-insecure-requests": [],
        }
        
        if settings.DEBUG:
            # Relaxed policy for development
            directives["connect-src"].extend([
                "ws://localhost:*",
                "http://localhost:*",
            ])
        
        policy_parts = []
        for directive, sources in directives.items():
            if sources:
                policy_parts.append(f"{directive} {' '.join(sources)}")
            else:
                policy_parts.append(directive)
        
        return "; ".join(policy_parts)
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Strict Transport Security (HSTS)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Type Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Frame Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        # Cross-Origin policies
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Remove server identification
        response.headers.pop("Server", None)
        
        return response


class CORSMiddleware:
    """Custom CORS middleware with strict controls."""
    
    ALLOWED_ORIGINS = [
        "https://revolutionx.com",
        "https://app.revolutionx.com",
        "https://admin.revolutionx.com",
    ]
    
    ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    ALLOWED_HEADERS = [
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "Accept",
        "Origin",
        "X-CSRF-Token",
    ]
    EXPOSED_HEADERS = [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ]
    
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        origin = request.headers.get("origin")
        
        # Check if origin is allowed
        allowed = origin in self.ALLOWED_ORIGINS or settings.DEBUG
        
        if request.method == "OPTIONS":
            # Preflight request
            headers = {
                "Access-Control-Allow-Origin": origin if allowed else "",
                "Access-Control-Allow-Methods": ", ".join(self.ALLOWED_METHODS),
                "Access-Control-Allow-Headers": ", ".join(self.ALLOWED_HEADERS),
                "Access-Control-Expose-Headers": ", ".join(self.EXPOSED_HEADERS),
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "600",
            }
            
            await send({
                "type": "http.response.start",
                "status": 204,
                "headers": [
                    [k.encode(), v.encode()] for k, v in headers.items()
                ],
            })
            await send({"type": "http.response.body", "body": b""})
            return
        
        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                
                cors_headers = [
                    (b"access-control-allow-origin", origin.encode() if allowed else b""),
                    (b"access-control-allow-credentials", b"true"),
                    (b"access-control-expose-headers", ", ".join(self.EXPOSED_HEADERS).encode()),
                ]
                
                headers.extend(cors_headers)
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_with_cors)


class SecureCookieMiddleware(BaseHTTPMiddleware):
    """Ensure secure cookie settings."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        if "set-cookie" in response.headers:
            # Ensure secure flag is set
            cookie = response.headers["set-cookie"]
            if "secure" not in cookie.lower():
                response.headers["set-cookie"] = f"{cookie}; Secure"
            
            # Ensure HttpOnly flag is set
            if "httponly" not in cookie.lower():
                response.headers["set-cookie"] = f"{cookie}; HttpOnly"
            
            # SameSite attribute
            if "samesite" not in cookie.lower():
                response.headers["set-cookie"] = f"{cookie}; SameSite=Strict"
        
        return response
