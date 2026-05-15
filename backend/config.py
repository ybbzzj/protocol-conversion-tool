# -*- coding: utf-8 -*-
import os
import sys

class Config:
    # 1. 基础资源目录 (只读，随 exe 打包)
    if getattr(sys, 'frozen', False):
        # 如果是打包后的 exe，资源在 _MEIPASS 中
        RESOURCE_DIR = sys._MEIPASS
    else:
        # 开发环境下，资源在项目根目录
        RESOURCE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # 2. 数据持久化目录 (可写，在 exe 同级目录)
    if getattr(sys, 'frozen', False):
        # 打包后，数据存在 exe 所在的真实目录中，防止被临时清理
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = RESOURCE_DIR

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'backend', 'uploads')
    OUTPUT_FOLDER = os.path.join(BASE_DIR, 'backend', 'outputs')
    DATA_DIR = os.path.join(BASE_DIR, 'backend', 'data')
    
    # 知识库本地文件路径 (不再使用数据库)
    KNOWLEDGE_BASE_FILE = os.path.join(DATA_DIR, 'knowledge_base.json')
    
    # 字段配置文件路径 (属于只读资源，应从 RESOURCE_DIR 读取)
    PROTOCOL_FIELDS_PATH = os.path.join(RESOURCE_DIR, 'backend', 'config_protocol_fields.json')
    TARGET_FIELDS_PATH = os.path.join(RESOURCE_DIR, 'backend', 'config_target_fields.json')
    CONFIG_TEMPLATES_PATH = os.path.join(RESOURCE_DIR, 'backend', 'config_templates.json')
    
    # 新增的配置项
    KNOWLEDGE_BASE_PATH = KNOWLEDGE_BASE_FILE
    MAPPING_THRESHOLD = 0.7
    
    # 其他配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'protocol-tool-secret'
    ALLOWED_EXTENSIONS = {'docx', 'doc', 'xlsx'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
