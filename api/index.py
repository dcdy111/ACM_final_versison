# Vercel入口文件 - 将Flask应用适配为Vercel函数
import sys
import os

# 将项目根目录添加到Python路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # 导入Flask应用
    from app import app
    
    # 设置Vercel环境标识
    os.environ['VERCEL'] = '1'
    
    # 配置应用以适应Vercel环境
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # 禁用调试模式以确保生产环境稳定性
    app.config['DEBUG'] = False
    app.config['ENV'] = 'production'

    # 配置安全的密钥
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'vercel-production-key-2024')

    # 数据库初始化（简化版）
    try:
        from db_utils import init_db
        with app.app_context():
            init_db()
            print("✅ 数据库初始化完成")
    except Exception as db_error:
        print(f"⚠️ 数据库初始化警告: {db_error}")
        # 在生产环境中，数据库问题不应中断应用

    print("🔧 Vercel环境配置完成")

except Exception as e:
    print(f"❌ 应用初始化失败: {e}")
    import traceback
    traceback.print_exc()
    
    # 创建后备应用
    from flask import Flask, jsonify
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-key')
    
    @app.route('/')
    def fallback():
        return jsonify({
            'error': '应用启动失败',
            'message': str(e),
            'status': 'fallback_mode'
        })
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'error', 'message': 'Application failed to initialize'})

# 导出应用供Vercel使用
# Vercel会自动识别并调用这个应用
# 无需自定义handler函数

# 如果直接运行此文件，启动开发服务器
if __name__ == '__main__':
    print("🚀 本地开发模式启动")
    app.run(debug=False, host='0.0.0.0', port=5000)
