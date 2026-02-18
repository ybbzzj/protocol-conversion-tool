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
    from backend.routes.history import history_bp
    from backend.routes.batch import batch_bp
    from backend.routes.config import config_bp
    from backend.routes.templates import templates_bp
    from backend.routes.mapping import mapping_bp
    
    # ✅ 正确方式: 为每个蓝图指定完整的 url_prefix
    app.register_blueprint(extract_bp, url_prefix='/api/extract')
    app.register_blueprint(match_bp, url_prefix='/api/match')
    app.register_blueprint(knowledge_bp, url_prefix='/api/knowledge')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(history_bp, url_prefix='/api/history')
    app.register_blueprint(batch_bp, url_prefix='/api/batch')
    app.register_blueprint(config_bp, url_prefix='/api/config')
    app.register_blueprint(templates_bp, url_prefix='/api/templates')
    app.register_blueprint(mapping_bp, url_prefix='/api/mapping')
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'version': '2.0.0'}
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)
