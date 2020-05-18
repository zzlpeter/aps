from tornado.web import RequestHandler

from web.errors import AssassinException


class AssassinBaseHandler(RequestHandler):

    def initialize(self, middleware):
        self.middleware = middleware

    def prepare(self):
        for mid in self.middleware:
            mid.process_request(self)

    def finish_success(self, data=None):
        base = {
            'code': 200,
            'msg': 'success',
            'data': data
        }
        return self.write(base)

    def finish_error(self, msg):
        base = {
            'code': 400,
            'msg': msg
        }
        self.set_status(400)
        return self.write(base)

    def write_error(self, status_code, **kwargs):
        exc_cls, exc_instance, trace = kwargs.get('exc_info')
        if status_code != 200:
            if issubclass(exc_cls, AssassinException):
                status_code, exc_instance = exc_instance.args
            self.set_status(status_code)
            rtn = {
                'code': status_code,
                'msg': str(exc_instance)
            }
            return self.write(rtn)
