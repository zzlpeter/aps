**项目结构**
```
conf                    配置文件目录（需要配合 Dockerfile 里面 APP_ENV 变量）         
    local                   本地开发环境
        common.toml             通用配置
        logger.toml             日志文件配置
        mysql.toml              数据库配置
        redis.toml              Redis配置
    test                    测试环境
    online                  线上环境
libs                    库函数
    aps                     apscheduler - 不可修改
    decorators              装饰器
    logger                  日志
    mysql                   MySQL链接池
    redis                   Redis链接池
    requests                request orm
    tomlread                解析toml配置文件
    utils                   其他库函数
        datekit                 时间相关
        notice                  报警相关
        other                   其他
models                  models orm
tasks                   任务相关
    cron                    定时任务（标准cron格式）
    date                    定点任务
    interval                周期任务
Dockerfile              
main.py                 程序入口
requirements.txt
```

**初始化**
```
执行SQL
CREATE TABLE `task`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键自增',
  `task_key` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '任务唯一标识',
  `execute_func` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '任务执行的方法',
  `trigger` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '调度方式(cron/date/interval)',
  `spec` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '调度时间',
  `args` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '执行方法的args参数',
  `is_valid` int(11) NOT NULL COMMENT '是否有效',
  `status` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '执行状态(ready/doing)',
  `extra` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '{}' COMMENT '额外信息',
  `create_at` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  `update_at` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0) COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ux__task__task_key_status`(`task_key`, `status`) USING BTREE COMMENT 'task_key/status唯一索引'
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 ROW_FORMAT = Dynamic;

CREATE TABLE `execute_task`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键自增',
  `task_id` int(11) NOT NULL COMMENT '任务ID',
  `status` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '执行状态',
  `extra` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '{}' COMMENT '额外信息',
  `create_at` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  `update_at` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0) COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 ROW_FORMAT = Dynamic;

```

**特殊说明**
```
1、运行中的任务, 只允许修改 `is_valid`, `spec`; 其他信息修改之后框架不会识别
   `is_valid` 控制任务启停 （最多延迟10s生效）
   `spec` 控制任务调度时间（最多延迟10s生效）
2、tasks 目录下面定义的任务, 接受参数说明
   async def test_cron(task_key, *args, **kwargs):
       pass
   `task_key`: task表里定义的唯一标识
   `*args`: task表里定义的args参数
   `**kwargs`: {'sub_task_id': 当前执行子任务的主键}
```
