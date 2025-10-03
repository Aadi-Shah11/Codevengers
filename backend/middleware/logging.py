"""
Logging middleware for API requests
"""

import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests and responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} "
                f"in {process_time:.3f}s"
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"in {process_time:.3f}s - {str(e)}"
            )
            raise

class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log security-related events
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check for security-sensitive endpoints
        security_endpoints = [
            "/api/auth/verify_id",
            "/api/vehicles/verify",
            "/api/vehicles/upload_video",
            "/verify_id",  # Legacy endpoint
        ]
        
        is_security_endpoint = any(
            request.url.path.startswith(endpoint) 
            for endpoint in security_endpoints
        )
        
        if is_security_endpoint:
            # Log security request
            logger.info(
                f"Security Request: {request.method} {request.url.path} "
                f"from {request.client.host if request.client else 'unknown'}"
            )
        
        response = await call_next(request)
        
        if is_security_endpoint:
            # Log security response
            logger.info(
                f"Security Response: {response.status_code} "
                f"for {request.url.path}"
            )
        
        return response