"""
Rate Limiting and Security Middleware
"""
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict
import redis
import time
import structlog
from app.core.database import get_redis

logger = structlog.get_logger()

class RateLimiter:
    """Redis-based rate limiting with sliding window algorithm"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_limit = 100
        self.default_window = 3600  # 1 hour in seconds
    
    async def check_rate_limit(self, key: str, limit: int, window: int) -> tuple[bool, Dict]:
        """Check rate limit for a given key"""
        current_time = time.time()
        window_start = current_time - window
        
        # Clean old entries
        pattern = f"{key}:*"
        old_keys = self.redis.keys(pattern)
        for old_key in old_keys:
            try:
                timestamp = float(self.redis.get(old_key).decode())
                if timestamp < window_start:
                    self.redis.delete(old_key)
            except:
                continue
        
        # Count current window requests
        current_count = 0
        for old_key in old_keys:
            try:
                timestamp = float(self.redis.get(old_key).decode())
                if timestamp >= window_start:
                    current_count += 1
            except:
                continue
        
        if current_count >= limit:
            return False, {
                "limit": limit,
                "current": current_count,
                "remaining": max(0, limit - current_count),
                "reset_time": window_start + window,
            }
        
        # Record new request
        request_key = f"{key}:{current_time}"
        self.redis.set(request_key, current_time, ex=window)
        
        return True, {
            "limit": limit,
            "current": current_count + 1,
            "remaining": max(0, limit - current_count - 1),
            "reset_time": window_start + window,
        }
class SecurityMiddleware:
    """Comprehensive security middleware"""
    
    def __init__(self, app):
        self.app = app
        self.redis = redis.from_url("redis://localhost:6379/2", decode_responses=True)
        self.rate_limiter = RateLimiter(self.redis)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        client_ip = request.client.host
        path = request.url.path
        method = scope["method"]
        
        # Skip rate limiting for health checks and static files
        if path in ["/api/health", "/"] or path.startswith("/static"):
            await self.app(scope, receive, send)
            return
        
        # Apply rate limiting based on client IP and path
        key = f"rate_limit:{client_ip}:{path}"
        
        # Different limits for different endpoints
        if "/auth/" in path:
            limit, window = 10, 60  # 10 requests per minute for auth
        elif "/v1/chat" in path:
            limit, window = 50, 3600  # 50 requests per hour for chat
        else:
            limit, window = 100, 3600  # 100 requests per hour for others
        
        allowed, headers = await self.rate_limiter.check_rate_limit(key, limit, window)
        
        if not allowed:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": int(headers.get("reset_time", time.time()) - time.time()),
                    "limit": headers.get("limit"),
                    "current": headers.get("current"),
                    "remaining": headers.get("remaining"),
                },
                headers={
                    "X-RateLimit-Limit": str(headers.get("limit")),
                    "X-RateLimit-Remaining": str(headers.get("remaining")),
                    "X-RateLimit-Reset": str(headers.get("reset_time")),
                }
            )
            await response(scope, receive, send)
            return
        
        # Add security headers
        async def add_security_headers(send):
            response = await send()
            if response.status_code < 400:
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["X-Frame-Options"] = "DENY"
                response.headers["X-XSS-Protection"] = "1; mode=block"
                response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'"
            return response
        
        # Process request with security headers
        await self.app(scope, receive, add_security_headers)
class CircuitBreaker:
    """Circuit breaker pattern for service failures"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def record_success(self):
        """Record successful operation"""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def allow_request(self) -> bool:
        """Check if request is allowed"""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        
        if self.state == "HALF_OPEN":
            return True
        
        return False
