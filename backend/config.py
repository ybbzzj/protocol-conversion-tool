# -*- coding: utf-8 -*-
import os

class Config:
    # 基础目录配置
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'backend', 'uploads')
    OUTPUT_FOLDER = os.path.join(BASE_DIR, 'backend', 'outputs')
    DATA_DIR = os.path.join(BASE_DIR, 'backend', 'data')
    
    # 知识库本地文件路径 (不再使用数据库)
    KNOWLEDGE_BASE_FILE = os.path.join(DATA_DIR, 'knowledge_base.json')
    
    # 其他配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'protocol-tool-secret'
    ALLOWED_EXTENSIONS = {'docx', 'doc', 'xlsx'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
