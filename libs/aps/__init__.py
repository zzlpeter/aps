from functools import wraps
import traceback

from libs.utils.other import Environ, Host, gen_uuid
from libs.utils.notice import ding_ding_notice
from libs.utils.datekit import datetime_fmt, datetime2timestamp, now_timestamp
from libs.logger import LoggerPool
from libs.redis import redis_pools
from models.task import Task, TaskExecute

ip = Host().host_ip()
logger = LoggerPool.other


def lock(func):
    """
    to get lock in concurrent condition
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        task_key, *args = args
        # 判断环境变量
        is_killed = Environ().IS_KILLED
        if is_killed == 'KILLED':
            logger.info({'keyword': 'receive_sigterm', 'ip': ip})
            return

        # 生成trace_id
        __unique_trace_id__ = gen_uuid()

        # 执行原子操作
        execute_success, sub_task_id = Task.task_atomic_insert(task_key, __unique_trace_id__)

        # 任务是否已被执行
        if not execute_success:
            logger.info({'keyword': 'get_no_lock', 'ip': ip, 'task_key': task_key})
            return

        # 将当前子任务ID及trace_id更新至kwargs参数
        kwargs.update(sub_task_id=sub_task_id)
        kwargs.update(__unique_trace_id__=__unique_trace_id__)

        # 开始执行任务
        logger.info({'keyword': 'get_lock', 'ip': ip})
        status, ext = 'success', {}
        try:
            await func(task_key, *args, **kwargs)
        except Exception as e:
            logger.error({'panic_keyword': func.__name__, 'err': traceback.format_exc(),
                          'err_type': 'execute_task', 'ip': ip})
            status = 'fail'
            ext = {'err': traceback.format_exc()}

        # 更新父任务和子任务状态
        try:
            is_success, err = Task.task_atomic_update(task_key, sub_task_id, status, ext)
            if not is_success:
                await ding_ding_notice('执行任务{}, 更新任务状态失败: {}'.format(task_key, err))
        except Exception as e:
            logger.error({'panic_keyword': func.__name__, 'err': traceback.format_exc(),
                          'err_type': 'execute_task', 'ip': ip})
            await ding_ding_notice('执行任务{}异常：{}'.format(task_key, e))

    return wrapper


class TriggerOperate:
    @staticmethod
    def modify_trigger(trigger, spec, tid):
        """
        根据trigger生成调度任务
        """
        if trigger == 'date':
            if spec == 'now':
                _str = 'scheduler.reschedule_job("{}")'.format(tid)
            else:
                _str = 'scheduler.reschedule_job("{}", trigger="date", run_date="{}")'.format(tid, spec)
        elif trigger == 'interval':
            _str = 'scheduler.reschedule_job("{}", trigger="interval", seconds={})'.format(tid, spec)
        else:
            _str = 'scheduler.reschedule_job("{}", trigger=CronTrigger.from_crontab("{}"))'.format(tid, spec)
        return _str

    def add_trigger(self, trigger, spec, tid, execute_func, task_key, args):
        args = self.make_args(task_key, args)
        if trigger == 'date':
            if spec == 'now':
                _str = 'scheduler.add_job(lock({}), args=({},), id="{}")'.\
                    format(execute_func, args, tid)
            else:
                _str = 'scheduler.add_job(lock({}), "date", run_date="{}", args=({},), id="{}")'.\
                    format(execute_func, spec, args, tid)
        elif trigger == 'interval':
            _str = 'scheduler.add_job(lock({}), "interval", seconds={}, args=({},), id="{}")'.\
                format(execute_func, spec, args, tid)
        else:
            _str = 'scheduler.add_job(lock({}), trigger=CronTrigger.from_crontab("{}"), args=({},), id="{}")'.\
                format(execute_func, spec, args, tid)
        return _str

    @staticmethod
    def make_args(task_key, args):
        if type(args) is not str:
            args = ''
        if not args:
            return '"{}"'.format(task_key)
        args = args.replace('"', '').replace("'", '')
        args_list = args.split(',')
        args_with_double_quotes = ['"{}"'.format(arg) for arg in args_list]
        return '"{}",'.format(task_key) + ','.join(args_with_double_quotes)


async def monitor_tasks():
    """
    监控任务执行情况
    """
    rds = await redis_pools('default')
    # 允许多实例间最大误差为60s
    rst = await rds.set('assassin:unique:monitor_task', now_timestamp(), expire=60, exist='SET_IF_NOT_EXIST')
    if not rst:
        logger.info({'keyword': 'get_monitor_task_lock', 'ip': ip})
        return
    alarms = ['assassin任务执行异常, 详情如下：\n任务key -- 默认延迟s -- 最近执行']
    tasks = await Task.async_objects.execute(Task.select().where(Task.is_valid == 1))
    for t in tasks:
        sub = await TaskExecute.async_objects.execute(TaskExecute.select(TaskExecute.create_at,
                                                                         TaskExecute.extra, TaskExecute.id).
                                                      where(TaskExecute.task_id == t.id).
                                                      order_by(-TaskExecute.id).limit(1))
        for s in sub:
            # 最近执行时间
            bj = datetime_fmt(s.create_at)
            last_stamp = datetime2timestamp(s.create_at) - 8 * 3600
            delay = t.extra.get('delay', 3600)
            if now_timestamp() - last_stamp > delay:
                # 该报警是否已被处理
                if not s.extra.get('deal_alarm'):
                    alarms.append(f'{t.task_key} -- {delay} -- {bj}')
                    t.update_ext(alarm_sub_task=s.id)
            break
    if len(alarms) > 1:
        await ding_ding_notice('\n'.join(alarms))


async def reset_tasks_status():
    """
    程序退出之前更新所有doing状态任务为ready
    确保下次可以正常执行
    """
    logger.info('程序即将退出、重置任务状态')
    await Task.async_objects.execute(Task.update(status='ready').where(Task.is_valid == 1, Task.status == 'doing'))
