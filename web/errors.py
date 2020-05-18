class AssassinException(Exception):
    pass


class AuthorizationException(AssassinException):
    def __init__(self, msg):
        super(AuthorizationException, self).__init__(401, msg)


class BadRequestException(AssassinException):
    def __init__(self, msg):
        super(BadRequestException, self).__init__(400, msg)


class PermissionException(AssassinException):
    def __init__(self, msg):
        super(PermissionException, self).__init__(403, msg)
