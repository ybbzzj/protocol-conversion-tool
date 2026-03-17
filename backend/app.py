# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, send_from_directory, request, send_file
from flask_cors import CORS
from backend.config import config_by_name

def create_app(config_name='development'):
    # ✅ 指定静态文件目录为前端构建后的 dist 文件夹
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_folder = os.path.join(base_dir, 'public', 'dist')
    
    # ✅ 1. 初始化时禁用 static_folder，由我们手动托管以支持 SPA 路由
    app = Flask(__name__, static_folder=None)
    
    # 安全获取配置对象，兜底使用 development
    config_obj = config_by_name.get(config_name, config_by_name.get('development'))
    app.config.from_object(config_obj)
    
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
    
    # ✅ 2. 蓝图注册：保持原样，通过 /api 前缀区分
    app.register_blueprint(extract_bp, url_prefix='/api/extract')
    app.register_blueprint(match_bp, url_prefix='/api/match')
    app.register_blueprint(knowledge_bp, url_prefix='/api/knowledge')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(history_bp, url_prefix='/api/history')
    app.register_blueprint(batch_bp, url_prefix='/api/batch')
    app.register_blueprint(config_bp, url_prefix='/api/config')
    app.register_blueprint(templates_bp, url_prefix='/api/templates')
    app.register_blueprint(mapping_bp, url_prefix='/api/mapping')

    # ✅ 3. 手动托管所有路径 (实现 SPA 路由和下载接口兼容)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_all(path):
        # A. 兼容前端未加 /api 的下载请求 (如 /extract/download/...)
        if path.startswith('extract/download/'):
            # 重定向到正确的 API 路径
            from flask import redirect
            return redirect(f'/api/{path}')

        # B. 排除其他 /api/ 请求（由蓝图处理）
        if path.startswith('api/'):
            return {"error": f"API route '{path}' not found"}, 404
            
        # C. 静态文件请求 (assets/..., favicon.ico 等)
        if path != "":
            full_path = os.path.join(static_folder, path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                return send_from_directory(static_folder, path)
        
        # D. 兜底返回 index.html (支持 Vue Router History 模式)
        index_file = os.path.join(static_folder, 'index.html')
        if os.path.exists(index_file):
            return send_file(index_file)
        
        return f"Frontend dist not found at: {static_folder}", 404
    
    # 打印调试信息
    print(f"[App] 启动模式: 集成托管")
    print(f"[App] 静态目录: {static_folder}")
    print(f"[App] index.html: {'✅ 存在' if os.path.exists(os.path.join(static_folder, 'index.html')) else '❌ 不存在'}")
    
    # 预加载语义模型（在后台线程或启动时加载）
    def preload_model():
        try:
            from backend.services.embedding_service import embedding_service
            print("[App] 正在预加载语义模型...")
            # 简单调用一下，触发初始化
            embedding_service.get_embedding("初始化")
        except Exception as e:
            print(f"[App] 预加载语义模型失败: {e}")

    import threading
    threading.Thread(target=preload_model).start()
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'version': '2.0.0'}
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=False)
