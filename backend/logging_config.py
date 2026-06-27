# -*- coding: utf-8 -*-
"""集中式日志配置：同时输出到控制台与滚动文件，统一格式。"""
import os
import sys
import re
import logging
from logging.handlers import RotatingFileHandler
from backend.config import Config

_LOG_FORMAT = '%(asctime)s | %(levelname)-7s | %(name)s | %(message)s'
_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

_configured = False


class _AccessLogNoiseFilter(logging.Filter):
    """屏蔽 werkzeug 成功访问日志(2xx/3xx)，只保留出错请求(4xx/5xx)。

    favicon、静态资源、前端轮询等无用 GET 200/304 全部不再打印，
    业务关键节点由各模块的业务日志覆盖；请求出错(404/500)仍可见。
    """
    # 匹配访问行结尾的 HTTP 状态码： ... "GET /favicon.ico HTTP/1.1" 200 -
    _STATUS_RE = re.compile(r'"\s+(\d{3})\b')

    def filter(self, record):
        m = self._STATUS_RE.search(record.getMessage())
        if m and m.group(1)[0] in ('2', '3'):
            return False
        return True


def setup_logging(level=logging.INFO):
    """初始化根日志器。重复调用安全（只初始化一次）。"""
    global _configured
    if _configured:
        return logging.getLogger()

    os.makedirs(Config.LOG_DIR, exist_ok=True)
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    root = logging.getLogger()
    root.setLevel(level)

    # 控制台
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    # 滚动文件：单文件 5MB，保留 5 份
    file_handler = RotatingFileHandler(
        os.path.join(Config.LOG_DIR, 'app.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # 让 werkzeug 的 HTTP 访问日志走同一套 handler，并过滤轮询噪声
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers = []
    werkzeug_logger.propagate = True
    werkzeug_logger.addFilter(_AccessLogNoiseFilter())

    _configured = True
    logging.getLogger(__name__).info('日志系统已初始化，日志目录: %s', Config.LOG_DIR)
    return root
