import os
import sys
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)
sys.path.append(os.path.join(project_path, 'libs'))

import tornado.web
import tornado.locks
import tornado.ioloop
from tornado.options import define, options
from tornado_swagger.setup import setup_swagger

from web.api.task import TaskHandler, TasksHandler, SubTasksHandler
from web.middlewares import get_middleware

define("port", default=8888, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        middleware_tuple = get_middleware()

        handlers = [
            tornado.web.url('/assassin/tasks', TasksHandler, {'middleware': middleware_tuple}),
            tornado.web.url('/assassin/task', TaskHandler, {'middleware': middleware_tuple}),
            tornado.web.url('/assassin/sub_tasks', SubTasksHandler, {'middleware': middleware_tuple})
        ]
        setup_swagger(handlers, description='Assassin API Definition', title='Assassin API')
        super(Application, self).__init__(handlers)


async def main_web():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    shutdown_event = tornado.locks.Event()
    await shutdown_event.wait()


if __name__ == '__main__':
    tornado.ioloop.IOLoop.current().run_sync(main_web)
