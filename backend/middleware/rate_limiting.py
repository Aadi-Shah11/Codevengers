"""
Rate limiting middleware for API protection
"""

import time
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, Deque

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware based on client IP
    """
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # Number of calls allowed
        self.period = period  # Time period in seconds
        self.clients: Dict[str, Deque[float]] = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Current time
        now = time.time()
        
        # Clean old entries
        client_calls = self.clients[client_ip]
        while client_calls and client_calls[0] <= now - self.period:
            client_calls.popleft()
        
        # Check rate limit
        if len(client_calls) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {self.calls} per {self.period} seconds",
                    "retry_after": self.period
                }
            )
        
        # Add current request
        client_calls.append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(self.calls - len(client_calls))
        response.headers["X-RateLimit-Reset"] = str(int(now + self.period))
        
        return response

class SecurityRateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Stricter rate limiting for security-sensitive endpoints
    """
    
    def __init__(self, app, calls: int = 10, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, Deque[float]] = defaultdict(deque)
        
        # Security-sensitive endpoints
        self.security_endpoints = [
            "/api/auth/verify_id",
            "/api/vehicles/verify",
            "/verify_id",  # Legacy endpoint
        ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Check if this is a security endpoint
        is_security_endpoint = any(
            request.url.path.startswith(endpoint) 
            for endpoint in self.security_endpoints
        )
        
        if not is_security_endpoint:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Current time
        now = time.time()
        
        # Clean old entries
        client_calls = self.clients[client_ip]
        while client_calls and client_calls[0] <= now - self.period:
            client_calls.popleft()
        
        # Check rate limit
        if len(client_calls) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Security rate limit exceeded",
                    "message": f"Too many security requests. Limit: {self.calls} per {self.period} seconds",
                    "retry_after": self.period
                }
            )
        
        # Add current request
        client_calls.append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add security rate limit headers
        response.headers["X-Security-RateLimit-Limit"] = str(self.calls)
        response.headers["X-Security-RateLimit-Remaining"] = str(self.calls - len(client_calls))
        response.headers["X-Security-RateLimit-Reset"] = str(int(now + self.period))
        
        return response