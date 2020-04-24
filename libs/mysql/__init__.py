"""
MySQL连接池管理
"""
import peewee_async

from libs.tomlread import ConfEntity
from libs.decorators import singleton
from libs.utils.other import dict2obj


__all__ = [
    'MysqlPools'
]


@singleton
class Mysql:
    mysql_pools = {}

    def __init__(self):
        pass

    def create_pool(self):
        _mysql_pools = {}
        mysql_conf = ConfEntity().mysql
        for alias, cnf in mysql_conf.items():
            db = cnf.pop('db')
            is_async = cnf.pop('is_async', False)
            db_conn = peewee_async.PooledMySQLDatabase(db, **cnf)
            # 是否异步操作
            # if not bool(is_async):
            # db_conn.set_allow_sync(False)
            db_conn.allow_sync()
            manager = peewee_async.Manager(db_conn)
            # 每个链接对象有两个属性：.db_conn  .manager
            _mysql_pools[alias] = dict2obj(dict(db_conn=db_conn, manager=manager))
        self.mysql_pools = _mysql_pools

    @property
    def pools(self):
        if not self.mysql_pools:
            self.create_pool()
        return self.mysql_pools


@singleton
class MysqlWrapper:
    pools = Mysql().pools

    def __getattr__(self, key):
        return self.pools.get(key)


MysqlPools = MysqlWrapper()


# class AppRouter:
#     @staticmethod
#     def db_for_operation(model):
#         meta = getattr(model, 'Meta')
#         if not meta:
#             raise Exception('model: <{}> not define Meta'.format(model.__name__))
#         db_label = getattr(model.Meta, 'db_label', 'default')
#         return Engines().get_engine(db_label)
#
#
# class BaseModelMix(peewee.Model):
#     @classmethod
#     def manager(cls):
#         db_info = AppRouter.db_for_operation(cls)
#         return db_info['manager']
#
#     @classmethod
#     def db_conn(cls):
#         db_info = AppRouter.db_for_operation(cls)
#         return db_info['db_conn']
