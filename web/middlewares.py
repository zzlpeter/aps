from web.errors import AuthorizationException, PermissionException

class Middleware:
    def process_request(self, handler):
        pass

    def process_response(self, handler):
        pass


class PermsMiddleware(Middleware):
    """
    是否有权限 - 403
    """
    @staticmethod
    def has_perm(hanlder):
        path = hanlder.path
        pass

    def process_request(self, handler):
        return self.has_perm(handler)


class AuthMiddleware(Middleware):
    """
    是否登录 - 401
    """
    @staticmethod
    def is_login(handler):
        session_id = handler.get_cookie('SESSION_ID')
        # 处理session信息
        if not session_id:
            raise AuthorizationException('please login')
        # 登录成功之后set user对象

    def process_request(self, handler):
        # print('auth middleware ...')
        return self.is_login(handler)


def get_middleware():
    return (
        # AuthMiddleware(),
        # PermsMiddleware(),
    )
