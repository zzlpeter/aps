from functools import wraps
import traceback

from libs.utils.other import Environ, Host
from libs.utils.notice import ding_ding_notice
from libs.logger import LoggerPool
from models.task import Task

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

        # 执行原子操作
        execute_success, sub_task_id = Task.task_atomic_insert(task_key)

        # 任务是否已被执行
        if not execute_success:
            logger.info({'keyword': 'get_no_lock', 'ip': ip, 'task_key': task_key})
            return

        # 将当前任务对象及session更新至kwargs参数
        kwargs.update(sub_task_id=sub_task_id)

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
        return '"{}",'.format(task_key) + args
