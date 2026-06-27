# -*- coding: utf-8 -*-
"""集中式日志配置：同时输出到控制台与滚动文件，统一格式。"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from backend.config import Config

_LOG_FORMAT = '%(asctime)s | %(levelname)-7s | %(name)s | %(message)s'
_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

_configured = False


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

    # 让 werkzeug 的 HTTP 访问日志走同一套 handler，避免重复输出
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers = []
    werkzeug_logger.propagate = True

    _configured = True
    logging.getLogger(__name__).info('日志系统已初始化，日志目录: %s', Config.LOG_DIR)
    return root
