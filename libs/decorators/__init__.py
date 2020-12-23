from functools import wraps
import traceback
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor


def try_catch(func):
    """
    捕获异常装饰器
    """
    from libs.logger import LoggerPool
    logger = LoggerPool.other

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
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


class AsyncModuleWrapper:
    """
    PS:
    实现原理是多线程
    建议直接使用原生异步的库函数、不要过度依赖该装饰器

    使用方法如下:
    import time
    async main():
        async_time = AsyncWrapper(time)
        await async_time.sleep(10)
    """
    def __init__(self, module, *, loop=None, max_workers=1):
        self.module = module
        self.loop = loop or asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def __getattr__(self, name):
        origin = getattr(self.module, name)
        if callable(origin):
            async def foo(*args, **kwargs):
                return await self.run(origin, *args, **kwargs)

            # 缓存刚刚构建的可调用对象
            self.__dict__[name] = foo
            return foo
        return origin

    async def run(self, origin_func, *args, **kwargs):
        def wrapper():
            return origin_func(*args, **kwargs)

        return await self.loop.run_in_executor(self.executor, wrapper)
