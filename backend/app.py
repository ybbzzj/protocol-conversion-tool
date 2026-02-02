# -*- coding: utf-8 -*-
from flask import Flask
from flask_cors import CORS
from backend.config import config_by_name

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # 启用跨域
    CORS(app)
    
    # 注册蓝图
    from backend.routes.extract import extract_bp
    from backend.routes.match import match_bp
    from backend.routes.knowledge import knowledge_bp
    from backend.routes.dashboard import dashboard_bp
    
    app.register_blueprint(extract_bp, url_prefix='/api')
    app.register_blueprint(match_bp, url_prefix='/api')
    app.register_blueprint(knowledge_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp, url_prefix='/api')
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'version': '2.0.0'}
        
    return app
