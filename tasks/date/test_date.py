"""
测试date
"""
from datetime import datetime


async def test_date(task_key, *args, **kwargs):
    print('test-date, datetime: ', datetime.now(), 'task-key:', task_key, 'args: ', args, 'kwargs: ', kwargs)
    raise Exception("test raise")
