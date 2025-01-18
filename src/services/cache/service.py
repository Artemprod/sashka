from functools import wraps

from aiocache import caches
from loguru import logger


def redis_cache_decorator(key: str, ttl: int = 300):
    """
    Кастомный декоратор для кеширования с использованием aiocache RedisCache.

    :param key: Ключ для кеша.
    :param ttl: Время жизни кеша (в секундах).
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = caches.get("default")

            # Генерация ключа (вставка в шаблон значений)
            func_params = func.__code__.co_varnames[:func.__code__.co_argcount]
            arg_dict = dict(zip(func_params, args))
            arg_dict.update(kwargs)
            generated_key = key.format(**arg_dict)

            cached_value = await cache.get(generated_key)
            if cached_value is not None:
                logger.info(f"Cache get: {generated_key} - {cached_value}")
                return cached_value

            result = await func(*args, **kwargs)

            await cache.set(generated_key, result, ttl=ttl)
            logger.info(f"Cache set: {generated_key} - {result}")
            return result

        return wrapper

    return decorator
