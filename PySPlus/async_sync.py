import asyncio
from functools import wraps

def async_to_sync(func):
    """دکوراتور برای تبدیل تابع async به sync"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
            async def coro_wrapper():
                return await func(*args, **kwargs)
            return coro_wrapper()
        except RuntimeError:
            return asyncio.run(func(*args, **kwargs))
    return wrapper