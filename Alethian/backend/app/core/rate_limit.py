from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_real_ip(request: Request):
    """Safely extract the client IP even if behind a proxy like Nginx."""
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    if "x-real-ip" in request.headers:
        return request.headers["x-real-ip"]
    return get_remote_address(request)

limiter = Limiter(key_func=get_real_ip)
