import hmac
import hashlib
from redis.asyncio import Redis
from app.core.config import get_settings
from app.core.errors import RateLimitError, ServiceUnavailableError

async def check_login_throttle(redis_client: Redis, email: str, ip_address: str) -> None:
    settings = get_settings()
    secret = settings.throttle_pseudonym_secret.encode()
    
    # Pseudonymise email and IP via HMAC
    email_hash = hmac.new(secret, email.lower().encode(), hashlib.sha256).hexdigest()
    ip_hash = hmac.new(secret, ip_address.encode(), hashlib.sha256).hexdigest()
    
    email_key = f"throttle:email:{email_hash}"
    ip_key = f"throttle:ip:{ip_hash}"
    
    window = settings.throttle_window_minutes * 60
    
    # We use a pipeline for atomicity
    # Increment counter, set TTL if it's new
    async with redis_client.pipeline(transaction=True) as pipe:
        try:
            pipe.incr(email_key)
            pipe.expire(email_key, window, nx=True)
            pipe.incr(ip_key)
            pipe.expire(ip_key, window, nx=True)
            results = await pipe.execute()
        except Exception:
            raise ServiceUnavailableError("Redis is unavailable for throttling") from None

    email_count, _, ip_count, _ = results
    
    if email_count > settings.throttle_max_email_attempts:
        raise RateLimitError("Too many login attempts for this account.")
        
    if ip_count > settings.throttle_max_ip_attempts:
        raise RateLimitError("Too many login attempts from this IP address.")

async def clear_login_throttle(redis_client: Redis, email: str) -> None:
    """Clear email throttle on successful login to avoid locking the user out."""
    settings = get_settings()
    secret = settings.throttle_pseudonym_secret.encode()
    email_hash = hmac.new(secret, email.lower().encode(), hashlib.sha256).hexdigest()
    email_key = f"throttle:email:{email_hash}"
    try:
        await redis_client.delete(email_key)
    except Exception:
        pass
