import os
import sys
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)
sys.path.append(os.path.join(project_path, 'libs'))

import signal
import traceback
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MAX_INSTANCES, EVENT_JOB_MISSED

from tasks import *
from models.task import Task
from libs.aps import lock, TriggerOperate
from libs.utils.other import Environ
from libs.utils.notice import ding_ding_notice
from libs.logger import LoggerPool

logger = LoggerPool.apscheduler
loop = asyncio.get_event_loop()
# 收到term信号之后最多等待10s、然后系统退出
timeout = 10
# scheduler参数配置
# https://www.jianshu.com/p/4f5305e220f0
job_defaults = {
    'coalesce': True,  # 是否允许合并多个哑弹
    'max_instances': 1,
    'misfire_grace_time': 60
}

# scheduler实例
scheduler = AsyncIOScheduler(job_defaults=job_defaults)
tasks_mapper = {
    # 'task.id_task.task_key': {
    #      'spec': task.spec
    # }
}


def err_listener(ev):
    """
    异常监听事件
    """
    msg = ''
    if ev.code == EVENT_JOB_ERROR:
        msg = ev.traceback
    elif ev.code == EVENT_JOB_MISSED:
        msg = 'missed job, job_id: %s, schedule_run_time: %s' % (ev.job_id, ev.scheduled_run_time)
    elif ev.code == EVENT_JOB_MAX_INSTANCES:
        msg = 'reached maximum of running instances, job_id: %s' % ev.job_id
    logger.error({'panic_keyword': 'program_error', 'err': msg, 'err_type': ev.code})


async def sync_schedule_task():
    """
    同步数据库定时任务到 apschedule
    """
    Task.connect()
    tasks = Task.select()
    for t in tasks:
        tid = '{}_{}'.format(t.id, t.task_key)
        job = scheduler.get_job(tid)
        # 移除任务
        if t.is_valid == 0:
            tasks_mapper.pop(tid, None)
            if not job:
                continue
            try:
                scheduler.remove_job(tid)
                logger.info({'keyword': 'remove_job', 'job_id': tid})
            except Exception as e:
                logger.error({'panic_keyword': 'remove_job_err', 'err': traceback.format_exc()})
                await ding_ding_notice('移除任务{}异常: {}'.format(tid, e))
            continue
        task_conf = tasks_mapper.get(tid, {})
        # 任务已存在 - 检查调度时间是否改变
        if job:
            # 调度方式未改变
            if task_conf.get('spec') == t.spec:
                continue
            evl_task = TriggerOperate.modify_trigger(t.trigger, t.spec, tid)
            try:
                exec(evl_task)
            except Exception as e:
                logger.error({'panic_keyword': 'reschedule_job_err', 'err': traceback.format_exc()})
                await ding_ding_notice('更新任务{}异常: {}'.format(tid, e))
            tasks_mapper[tid] = {
                'spec': t.spec
            }
            logger.info({'keyword': 'modify_job', 'job_id': tid})
            continue
        # 新创建任务
        evl_task = TriggerOperate().add_trigger(t.trigger, t.spec, tid, t.execute_func, t.task_key, t.args)
        try:
            eval(evl_task)
        except Exception as e:
            logger.error({'panic_keyword': 'sync_schedule_task_err', 'err': traceback.format_exc()})
            await ding_ding_notice('新增任务{}异常: {}'.format(tid, e))
        tasks_mapper[tid] = {
            'spec': t.spec
        }
        logger.info({'keyword': 'add_job', 'job_id': tid})
    Task.close()


async def shutdown():
    await asyncio.sleep(timeout)
    # 等待timeout秒之后退出主程序（确保scheduler中的程序全部执行完毕）
    os._exit(0)


def signal_handler(signalnum, frame):
    """
    优雅退出  kill -15
    """
    logger.info('dawn cron-task receive term signal')
    # 设置环境变量
    Environ().IS_KILLED = 'KILLED'
    # 等待所有任务执行完成之后再退出（优雅关闭）
    asyncio.ensure_future(shutdown())


if __name__ == '__main__':
    # to catch term signal
    signal.signal(signal.SIGTERM, signal_handler)
    # to run web api background
    os.system('python {} &'.format(os.path.join(project_path, 'web.py')))
    # run scheduler main process
    scheduler.add_listener(err_listener, EVENT_JOB_MAX_INSTANCES | EVENT_JOB_MISSED | EVENT_JOB_ERROR)
    # scheduler.add_job(sync_schedule_task, trigger=CronTrigger.from_crontab('* * * * *'), id='sync_task')
    scheduler.add_job(sync_schedule_task, 'interval', seconds=10, id='sync_task_all')

    scheduler.start()

    try:
        loop.run_forever()
    except Exception as e:
        logger.error('dawn cron-task err:{}'.format(e))
        os._exit(0)
