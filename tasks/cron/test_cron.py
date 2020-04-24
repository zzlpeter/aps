"""
测试cron
"""
from datetime import datetime


async def test_cron(task_key, *args, **kwargs):
    print('test-cron, datetime: ', datetime.now(), 'task-key:', task_key, 'args: ', args, 'kwargs: ', kwargs)
