"""
任务相关model
"""
from copy import deepcopy

import peewee

from libs.mysql import MysqlPools
from . import JsonField


class Task(peewee.Model):
    """
    任务表
    """
    trigger_choices = (
        ('interval', 'interval'),
        ('date', 'date'),
        ('cron', 'cron')
    )

    id = peewee.IntegerField()
    task_key = peewee.CharField()
    desc = peewee.CharField()
    execute_func = peewee.CharField()
    trigger = peewee.CharField(choices=trigger_choices)
    spec = peewee.CharField()
    args = peewee.CharField()
    is_valid = peewee.IntegerField()
    status = peewee.CharField()
    extra = JsonField()
    create_at = peewee.DateTimeField()
    update_at = peewee.DateTimeField()

    class Meta:
        database = MysqlPools.default.db_conn
        # MysqlPools之所有有default属性、是在mysql.toml里配置的
        db_table = 'task'

    @classmethod
    def task_atomic_insert(cls, task_key, trace_id):
        db = cls._meta.database
        execute_success = False
        sub_task_id = None
        with db.atomic() as trans:
            try:
                task = cls.select().where(cls.task_key == task_key, cls.status == 'ready', cls.is_valid == 1).for_update()
                task_id = task[0].id
                cls.update(status='doing').where(Task.task_key == task_key).execute()
                sub = TaskExecute.create(task_id=task_id, status='todo', extra={}, trace_id=trace_id)
                trans.commit()
                sub_task_id = sub.id
                execute_success = True
            except Exception as e:
                print(e)
                trans.rollback()
        return execute_success, sub_task_id

    @classmethod
    def task_atomic_update(cls, task_key, sub_task_id, status, _ext):
        db = cls._meta.database
        is_success, err = True, None
        with db.atomic() as trans:
            try:
                cls.update(status='ready').where(Task.task_key == task_key).execute()
                sub = TaskExecute.select().where(TaskExecute.id == sub_task_id).get()
                ext = deepcopy(sub.extra)
                ext.update(**_ext)
                sub.update(extra=ext, status=status).where(TaskExecute.id == sub_task_id).execute()
                trans.commit()
            except Exception as e:
                is_success, err = False, e
                trans.rollback()
        return is_success, err

    def update_ext(self, tk=None, **kwargs):
        if self.id is None and tk is None:
            raise Exception('Can not update empty instance')
        if self.id is not None:
            instance = self
        else:
            instance = self.select().where(Task.task_key == tk).get()
        ext = deepcopy(instance.extra)
        ext.update(**kwargs)
        instance.update(extra=ext).execute()


class TaskExecute(peewee.Model):
    """
    任务执行表
    """
    id = peewee.IntegerField(help_text='主键自增')
    task_id = peewee.IntegerField(help_text='任务ID')
    status = peewee.CharField(help_text='执行状态')
    extra = JsonField(help_text='额外信息(json格式)', default={})
    trace_id = peewee.CharField(help_text='trace_id')
    create_at = peewee.DateTimeField()
    update_at = peewee.DateTimeField()

    class Meta:
        database = MysqlPools.default.db_conn
        db_table = 'execute_task'

    def update_ext(self, pk=None, **kwargs):
        if self.id is None and pk is None:
            raise Exception('Can not update empty instance')
        if self.id is not None:
            instance = self
            pk = self.id
        else:
            instance = self.select().where(TaskExecute.id == pk).get()
        ext = deepcopy(instance.extra)
        ext.update(**kwargs)
        instance.update(extra=ext).where(TaskExecute.id == pk).execute()
