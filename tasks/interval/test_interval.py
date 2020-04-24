"""
测试interval
"""
from datetime import datetime


async def test_interval(task_key, *args, **kwargs):
    print('test-interval, datetime: ', datetime.now(), 'task-key:', task_key, 'args: ', args, 'kwargs:', kwargs)
