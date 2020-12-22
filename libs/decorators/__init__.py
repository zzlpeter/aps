from functools import wraps
import traceback
import threading


def try_catch(func):
    """
    捕获异常装饰器
    """
    from libs.logger import LoggerPool
    logger = LoggerPool.other

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.error('%s_err' % func.__name__, err=traceback.format_exc(), err_type='try_catch_decorator')

    return wrapper


def try_catch_async(func):
    """
    捕获异常装饰器 -- 异步
    """
    from libs.logger import LoggerPool
    logger = LoggerPool.other

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error('%s_err' % func.__name__, err=traceback.format_exc(), err_type='try_catch_decorator')

    return wrapper


def singleton(cls):
    """
    类单例模式 - 线程安全
    """
    instance = {}
    lock = threading.Lock()

    @wraps(cls)
    def _single(*args, **kwargs):
        with lock:
            if cls not in instance:
                instance[cls] = cls(*args, **kwargs)
        return instance[cls]

    return _single
