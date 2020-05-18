import json
from tornado_swagger.model import register_swagger_model

from models.task import TaskExecute, Task
from libs.utils.datekit import datetime_fmt
from web.errors import BadRequestException
from . import AssassinBaseHandler


class TasksHandler(AssassinBaseHandler):
    async def get(self, *args, **kwargs):
        """
        ---
        tags:
            - Tasks
        summary: Get all tasks
        description: get all tasks available
        produces:
            - application/json
        parameters:
            - in: "query"
              name: page
              description: 页码(默认1)
              required: true
              type: integer
              default: 1
            - in: "query"
              name: size
              description: 每页展示条数(默认20)
              required: true
              type: integer
              default: 20
        responses:
            200:
              description: list of tasks
              schema:
                $ref: '#/definitions/TaskModel'
            400:
              description: page and size should be int
        """
        page = self.get_argument('page', '1')
        size = self.get_argument('size', '20')
        if not page.isdigit() or not size.isdigit():
            raise BadRequestException('page and size should be int')
        query = Task.select().order_by(-Task.id)
        cnt = query.count()
        tasks = query.paginate((int(page) - 1) * int(size), int(size)).dicts()
        tasks = list(tasks)
        for task in tasks:
            task['create_at'] = datetime_fmt(task['create_at'])
            task['update_at'] = datetime_fmt(task['update_at'])
        rst = {
            'page': page,
            'size': size,
            'total': cnt,
            'data': tasks
        }
        return self.finish_success(rst)


class TaskHandler(AssassinBaseHandler):
    async def get(self, *args, **kwargs):
        """
        ---
        tags:
            - Tasks
        summary: Get special tasks
        description: get special task with task_id
        produces:
            - application/json
        parameters:
            -   name: task_id
                in: query
                description: task_id
                required: true
                type: integer
        responses:
            200:
              description: object of task
              schema:
                $ref: '#/definitions/TaskModel'
            400:
              description: task_id is invalid
        """
        pk = self.get_argument('task_id', '')
        query = Task.select().filter(Task.id == pk)
        if not query.exists():
            raise BadRequestException('task_id: `{}` is invalid'.format(pk))
        task = query.dicts().get()
        task['create_at'] = datetime_fmt(task['create_at'])
        task['update_at'] = datetime_fmt(task['update_at'])
        return self.finish_success(task)

    async def post(self):
        """
        ---
        tags:
            - Tasks
        summary: Add special task
        description: add special task
        parameters:
            -   name: task_key
                in: formData
                description: 任务唯一key
                required: true
                type: string
            -   name: desc
                in: formData
                description: 任务描述
                required: true
                type: string
            -   name: status
                in: formData
                description: 执行状态
                required: true
                type: string
                enum: [ready, doing]
            -   name: execute_func
                in: formData
                description: 执行方法
                required: true
                type: string
            -   name: trigger
                in: formData
                description: 触发类型
                required: true
                type: string
                enum: [interval, date, cron]
            -   name: spec
                in: formData
                description: 触发时间(与trigger配合使用)
                required: true
                type: string
            -   name: args
                in: formData
                description: args
                required: false
                type: string
                default: ""
            -   name: is_valid
                in: formData
                description: 是否有效
                required: true
                type: integer
                enum: [0, 1]
                default: 0
            -   name: extra
                in: formData
                description: 额外信息
                required: true
                type: string
                default: {}
        responses:
            200:
              description: task object
              schema:
                $ref: '#/definitions/TaskModel'
            400:
              description: params invalid
        """
        trigger = self.get_argument('trigger')
        spec = self.get_argument('spec', '')
        err, sp = self.trigger_validate(trigger, spec)
        if err is not None:
            raise BadRequestException('Trigger:`{}` and Spec:`{}` does not match'.format(trigger, spec))
        task_key = self.get_argument('task_key')
        task = Task.select().filter(Task.task_key == task_key).first()
        if task:
            raise BadRequestException('task_key: `{}` has existed, pls retry'.format(task_key))
        execute_func = self.get_argument('execute_func')
        is_valid = self.get_argument('is_valid')
        args = self.get_argument('args', '')
        desc = self.get_argument('desc', '')
        status = self.get_argument('status')
        extra = self.get_argument('extra', "{}")
        extra = json.loads(extra)
        tt = Task.create(task_key=task_key, execute_func=execute_func, trigger=trigger, spec=spec,
                         args=args, is_valid=is_valid, status=status, extra=extra, desc=desc)
        return self.finish_success(tt.id)

    async def put(self, *args, **kwargs):
        """
        ---
        tags:
            - Tasks
        summary: Update special task
        description: update special task
        parameters:
            -   name: task_id
                in: formData
                description: task_id
                required: true
                type: string
            -   name: desc
                in: formData
                description: 任务描述
                required: true
                type: string
            -   name: status
                in: formData
                description: 执行状态
                required: true
                type: string
                enum: [ready, doing]
            -   name: trigger
                in: formData
                description: 触发类型
                required: true
                type: string
                enum: [interval, date, cron]
            -   name: spec
                in: formData
                description: 触发时间(与trigger配合使用)
                required: true
                type: string
            -   name: args
                in: formData
                description: args
                required: false
                type: string
                default: ""
            -   name: is_valid
                in: formData
                description: 是否有效
                required: true
                type: integer
                enum: [0, 1]
                default: 0
            -   name: extra
                in: formData
                description: 额外信息
                required: true
                type: string
                default: {}
        responses:
            200:
              description: task object
              schema:
                $ref: '#/definitions/TaskModel'
            400:
              description: params invalid
        """
        trigger = self.get_argument('trigger')
        spec = self.get_argument('spec', '')
        err, sp = self.trigger_validate(trigger, spec)
        if err is not None:
            raise BadRequestException('Trigger:`{}` and Spec:`{}` does not match'.format(trigger, spec))
        task_id = self.get_argument('task_id')
        task = Task.select().filter(Task.id == task_id).first()
        if not task:
            raise BadRequestException('task_id: `{}` is invalid'.format(task_id))
        is_valid = self.get_argument('is_valid')
        args = self.get_argument('args', '')
        desc = self.get_argument('desc', '')
        status = self.get_argument('status')
        extra = self.get_argument('extra', "{}")
        extra = json.loads(extra)
        # save to db
        task.trigger = trigger
        task.desc = desc
        task.spec = sp
        task.is_valid = is_valid
        task.status = status
        task.args = args
        task.extra = extra
        task.save()
        return self.finish_success()

    @staticmethod
    def trigger_validate(trigger, spec):
        if trigger not in ('interval', 'date', 'cron'):
            return 'fail', spec

        def interval(sp):
            try:
                return None, int(sp)
            except Exception as e:
                return e, sp

        def cron(sp):
            from apscheduler.triggers.cron import CronTrigger
            try:
                CronTrigger.from_crontab(sp)
                return None, sp
            except Exception as e:
                return e, sp

        def date(sp):
            from libs.utils.datekit import datestr2bjdatetime
            try:
                datestr2bjdatetime(sp)
                return None, sp
            except Exception as e:
                return e, sp

        return {
            'interval': interval,
            'cron': cron,
            'date': date
        }[trigger](spec)


class SubTasksHandler(AssassinBaseHandler):
    async def get(self, *args, **kwargs):
        """
        ---
        tags:
            - Tasks
        summary: Get sub tasks
        description: get special sub tasks with task_id
        produces:
            - application/json
        parameters:
            -   name: task_id
                in: query
                description: 任务ID
                required: true
                type: integer
            -   name: page
                in: query
                description: 页码(默认1)
                required: true
                type: integer
                default: 1
            -   name: size
                in: query
                description: 每页展示条数(默认20)
                required: true
                type: integer
                default: 20
        responses:
            200:
              description: list of tasks
              schema:
                $ref: '#/definitions/SubTaskModel'
            400:
              description: page and size should be int
        """
        task_id = self.get_argument('task_id')
        page = self.get_argument('page', '1')
        size = self.get_argument('size', '20')
        if not page.isdigit() or not size.isdigit():
            raise BadRequestException('page and size should be int')
        query = TaskExecute.select().filter(TaskExecute.task_id == task_id).order_by(-TaskExecute.id)
        cnt = query.count()
        subs = query.paginate((int(page) - 1) * int(size), int(size)).dicts()
        subs = list(subs)
        for sub in subs:
            sub['create_at'] = datetime_fmt(sub['create_at'])
            sub['update_at'] = datetime_fmt(sub['update_at'])
        rst = {
            'page': page,
            'size': size,
            'total': cnt,
            'data': subs
        }
        return self.finish_success(rst)


@register_swagger_model
class TaskModel:
    """
    ---
    type: object
    description: Task model representation
    properties:
        id:
            type: integer
        task_key:
            type: string
        execute_func:
            type: string
        trigger:
            type: string
        spec:
            type: string
        args:
            type: string
        is_valid:
            type: integer
        status:
            type: string
        extra:
            type: string
        create_at:
            type: string
        update_at:
            type: string
    """


@register_swagger_model
class SubTaskModel:
    """
    ---
    type: object
    description: SubTask model representation
    properties:
        id:
            type: integer
        status:
            type: string
        extra:
            type: string
        create_at:
            type: string
        update_at:
            type: string
    """
