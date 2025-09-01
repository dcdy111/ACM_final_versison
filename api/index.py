# Vercel入口文件 - 将Flask应用适配为Vercel函数
import sys
import os

# 将项目根目录添加到Python路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入Flask应用
from app import app, socketio
from werkzeug.middleware.proxy_fix import ProxyFix

# 配置应用以适应Vercel环境
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# 禁用调试模式以确保生产环境稳定性
app.config['DEBUG'] = False
app.config['ENV'] = 'production'

# 配置安全的密钥（在Vercel中应通过环境变量设置）
if not app.config.get('SECRET_KEY'):
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# 初始化数据库（如果需要）
try:
    from db_utils import init_db
    with app.app_context():
        init_db()
        print("✅ 数据库初始化完成")
except Exception as e:
    print(f"⚠️ 数据库初始化警告: {e}")

# Vercel函数处理程序
def handler(request):
    """
    Vercel函数的主要处理程序
    这个函数会被Vercel调用来处理所有HTTP请求
    """
    return app(request.environ, lambda status, headers: None)

# 确保SocketIO在无服务器环境中正确工作
# 注意：Vercel的无服务器函数不支持WebSocket长连接
# 如果需要实时功能，建议使用Vercel的实时功能或外部服务
try:
    # 在生产环境中禁用SocketIO的某些功能
    socketio.init_app(app, cors_allowed_origins="*", 
                     async_mode='threading',
                     logger=False, 
                     engineio_logger=False)
except Exception as e:
    print(f"⚠️ SocketIO配置警告: {e}")

# 导出应用供Vercel使用
app = app

# 如果直接运行此文件，启动开发服务器
if __name__ == '__main__':
    print("🚀 本地开发模式启动")
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
