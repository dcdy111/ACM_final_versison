# Flask Web应用 - ACM实验室官网与后台管理系统

import secrets
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_from_directory, send_file, abort
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from werkzeug.utils import secure_filename
import sqlite3
import json
from datetime import datetime
from flask import Blueprint
from flask_socketio import SocketIO, emit
# 暂时注释掉有问题的API导入
from api.innovation import innovation_bp
# from api.notifications import notifications_bp
# from api.analytics import analytics_bp

# 添加缓存装饰器导入
from functools import lru_cache
import time

# 认证装饰器
def require_auth(f):
    """要求用户认证的装饰器，支持自动登录"""
    from functools import wraps
    from datetime import datetime, timedelta
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查当前登录状态
        if 'username' in session:
            return f(*args, **kwargs)
        
        # 检查自动登录标记和时间
        if session.get('auto_login_user') and session.get('auto_login_time'):
            auto_username = session.get('auto_login_user')
            auto_login_time = session.get('auto_login_time')
            
            try:
                login_time = datetime.fromisoformat(auto_login_time)
                if datetime.now() - login_time < timedelta(days=1):
                    # 在24小时内，尝试自动登录
                    user = get_user_by_username(auto_username)
                    if user:
                        # 自动登录成功
                        session['username'] = auto_username
                        session['role'] = user['role']
                        session.permanent = True
                        # 更新自动登录时间
                        session['auto_login_time'] = datetime.now().isoformat()
                        return f(*args, **kwargs)
                    else:
                        # 用户不存在，清除标记
                        session.pop('auto_login_user', None)
                        session.pop('auto_login_time', None)
                else:
                    # 超过24小时，清除标记
                    session.pop('auto_login_user', None)
                    session.pop('auto_login_time', None)
            except (ValueError, TypeError):
                # 时间格式错误，清除标记
                session.pop('auto_login_user', None)
                session.pop('auto_login_time', None)
        
        # 没有自动登录标记或已过期，跳转到登录页面
        return redirect(url_for('admin_login'))
    
    return decorated_function

# 简单的时间缓存装饰器
def timed_lru_cache(seconds: int = 300, maxsize: int = 128):
    def wrapper_cache(func):
        cached_func = lru_cache(maxsize=maxsize)(func)
        cached_func.lifetime = seconds
        cached_func.expiration = time.time() + cached_func.lifetime
        
        def wrapped_func(*args, **kwargs):
            if time.time() >= cached_func.expiration:
                cached_func.cache_clear()
                cached_func.expiration = time.time() + cached_func.lifetime
            return cached_func(*args, **kwargs)
        
        # 正确传递cache_clear方法
        wrapped_func.cache_clear = cached_func.cache_clear
        return wrapped_func
    return wrapper_cache

# 缓存数据库查询函数
@timed_lru_cache(seconds=300)  # 5分钟缓存
def get_all_team_members():
    """获取所有团队成员（带缓存）"""
    from db_utils import get_db
    
    with get_db() as conn:
        cursor = conn.execute('''
            SELECT * FROM team_members 
            ORDER BY order_index ASC, created_at DESC
        ''')
        members = cursor.fetchall()
        
        return [dict(member) for member in members]

@timed_lru_cache(seconds=300)  # 5分钟缓存
def get_all_papers():
    """获取所有论文（带缓存）"""
    from db_utils import get_db
    
    with get_db() as conn:
        # 获取所有论文
        cursor = conn.execute('''
            SELECT * FROM papers 
            ORDER BY order_index ASC, updated_at DESC
        ''')
        papers = cursor.fetchall()
        
        papers_data = []
        for paper in papers:
            paper_dict = dict(paper)
            
            # 从category_ids字段获取类别信息
            categories = paper_dict.get('category_ids', '[]')
            if isinstance(categories, str):
                try:
                    categories = json.loads(categories)
                except:
                    categories = []
            
            # 确保categories是列表格式
            if not isinstance(categories, list):
                categories = []
            
            paper_dict['categories'] = categories
            
            papers_data.append(paper_dict)
        
        return papers_data

def get_paper_by_id(paper_id: int):
    """根据ID获取论文"""
    from db_utils import get_db
    
    with get_db() as conn:
        # 获取论文基本信息
        paper = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
        
        if not paper:
            return None
        
        paper_dict = dict(paper)
        
        # 获取论文的类别信息
        category_relations = conn.execute("SELECT * FROM paper_category_relations WHERE paper_id = ?", (paper_id,)).fetchall()
        categories = []
        category_names = []
        category_levels = []
        
        for relation in category_relations:
            category = conn.execute("SELECT * FROM paper_categories WHERE id = ?", (relation['category_id'],)).fetchone()
            if category:
                categories.append(category['id'])
                category_names.append(category['name'])
                category_levels.append(category['level'])
        
        paper_dict['categories'] = categories
        paper_dict['category_names'] = category_names
        paper_dict['category_levels'] = category_levels
        
        return paper_dict

def create_paper(title: str, authors: list, journal: str = '', year: int = 2024, 
                abstract: str = '', category_ids: list = None, **kwargs):
    """创建新论文"""
    from db_utils import get_db
    
    with get_db() as conn:
        # 获取最大排序索引
        cursor = conn.execute('SELECT COALESCE(MAX(order_index), 0) FROM papers')
        max_order = cursor.fetchone()[0]
        
        # 准备论文数据
        paper_data = {
            'title': title,
            'authors': json.dumps(authors) if isinstance(authors, list) else str(authors),
            'journal': journal,
            'year': year,
            'abstract': abstract,
            'order_index': max_order + 1,
            'status': kwargs.get('status', 'published'),
            'pdf_url': kwargs.get('pdf_url', ''),
            'citation_count': kwargs.get('citation_count', 0),
            'doi': kwargs.get('doi', ''),
            'code_url': kwargs.get('code_url', ''),
            'video_url': kwargs.get('video_url', ''),
            'demo_url': kwargs.get('demo_url', ''),
            'category_ids': json.dumps(category_ids) if category_ids else '[]',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # 插入论文
        cursor = conn.execute('''
            INSERT INTO papers (title, authors, journal, year, abstract, order_index, 
                              status, pdf_url, citation_count, doi, code_url, video_url, 
                              demo_url, category_ids, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            paper_data['title'], paper_data['authors'], paper_data['journal'], 
            paper_data['year'], paper_data['abstract'], paper_data['order_index'],
            paper_data['status'], paper_data['pdf_url'], paper_data['citation_count'],
            paper_data['doi'], paper_data['code_url'], paper_data['video_url'],
            paper_data['demo_url'], paper_data['category_ids'], 
            paper_data['created_at'], paper_data['updated_at']
        ))
        
        paper_id = cursor.lastrowid
        conn.commit()
        
        # 清理缓存，确保下次获取数据时是最新的
        get_all_papers.cache_clear()
        
        return paper_id

def update_paper(paper_id: int, **kwargs):
    """更新论文信息"""
    from db_utils import get_db
    
    with get_db() as conn:
        # 检查论文是否存在
        cursor = conn.execute('SELECT * FROM papers WHERE id = ?', (paper_id,))
        if not cursor.fetchone():
            raise ValueError("论文不存在")
        
        # 准备更新数据
        update_fields = []
        update_values = []
        
        # 处理特殊字段
        if 'authors' in kwargs:
            authors = kwargs['authors']
            if isinstance(authors, list):
                update_fields.append('authors = ?')
                update_values.append(json.dumps(authors))
            else:
                update_fields.append('authors = ?')
                update_values.append(str(authors))
        
        # 处理其他字段
        for key in ['title', 'journal', 'year', 'abstract', 'status', 'pdf_url', 'citation_count', 'doi', 'code_url', 'video_url', 'demo_url']:
            if key in kwargs:
                update_fields.append(f'{key} = ?')
                update_values.append(kwargs[key])
        
        # 处理类别更新
        if 'category_ids' in kwargs:
            update_fields.append('category_ids = ?')
            update_values.append(json.dumps(kwargs['category_ids']) if kwargs['category_ids'] else '[]')
        
        # 添加更新时间
        update_fields.append('updated_at = ?')
        update_values.append(datetime.now().isoformat())
        
        # 添加论文ID到值列表
        update_values.append(paper_id)
        
        # 执行更新
        if update_fields:
            sql = f'UPDATE papers SET {", ".join(update_fields)} WHERE id = ?'
            conn.execute(sql, update_values)
            conn.commit()
        
        # 清理缓存
        get_all_papers.cache_clear()

def delete_paper(paper_id: int):
    """删除论文"""
    from db_utils import get_db
    
    with get_db() as conn:
        # 检查论文是否存在
        cursor = conn.execute('SELECT * FROM papers WHERE id = ?', (paper_id,))
        if not cursor.fetchone():
            raise ValueError("论文不存在")
        
        # 删除论文
        conn.execute('DELETE FROM papers WHERE id = ?', (paper_id,))
        conn.commit()
        
        # 清理缓存，确保下次获取数据时是最新的
        get_all_papers.cache_clear()

def reorder_papers(paper_ids: list):
    """重新排序论文"""
    from db_utils import get_db
    
    with get_db() as conn:
        for index, paper_id in enumerate(paper_ids):
            conn.execute('UPDATE papers SET order_index = ? WHERE id = ?', (index + 1, paper_id))
        conn.commit()
    
    # 清理缓存，确保下次获取数据时是最新的排序
    get_all_papers.cache_clear()
    print(f"✅ 论文排序已更新，缓存已清理")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', secrets.token_hex(16)),
    PERMANENT_SESSION_LIFETIME=timedelta(days=1),
    SESSION_REFRESH_EACH_REQUEST=True,
    JSON_AS_ASCII=False,  # 确保JSON中的中文字符正确显示
    SEND_FILE_MAX_AGE_DEFAULT=31536000,  # 启用静态文件缓存，1年过期
)

# 数据库配置 - 统一使用原生sqlite3
DATABASE = 'acm_lab.db'

# 移除SQLAlchemy配置
# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE}'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 移除SQLAlchemy初始化
# db.init_app(app)

# 初始化SocketIO - 检测环境
import os
is_vercel = os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV')

if is_vercel:
    # 在Vercel环境中创建一个虚拟SocketIO对象
    print("🔧 检测到Vercel环境，创建SocketIO兼容对象")
    class MockSocketIO:
        def __init__(self, app, **kwargs):
            pass
        def emit(self, event, data, **kwargs):
            print(f"Mock SocketIO emit: {event}")
        def on(self, event):
            def decorator(f):
                return f
            return decorator
        def init_app(self, app, **kwargs):
            pass
        def run(self, app, **kwargs):
            app.run(**kwargs)
    
    socketio = MockSocketIO(app, cors_allowed_origins="*")
else:
    # 本地开发环境使用真实SocketIO
    print("🚀 本地环境，初始化真实SocketIO")
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

app.extensions['socketio'] = socketio

# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    """客户端连接时触发"""
    print(f"客户端已连接: {request.sid}")
    from flask_socketio import join_room
    join_room('default')
    emit('connected', {'data': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接时触发"""
    print(f"客户端已断开: {request.sid}")
    from flask_socketio import leave_room, rooms
    # 从所有房间中移除客户端
    current_rooms = list(rooms())
    for room in current_rooms:
        if room != request.sid:  # 不要离开自己的房间
            leave_room(room)

@socketio.on('join_page')
def handle_join_page(data):
    """客户端加入特定页面"""
    page = data.get('page', 'home')
    print(f"客户端 {request.sid} 加入页面: {page}")
    from flask_socketio import join_room, leave_room, rooms
    # 先离开之前的页面房间
    current_rooms = list(rooms())
    for room in current_rooms:
        if room != request.sid and room != 'default':
            leave_room(room)
    # 加入新页面房间
    join_room(page)
    emit('joined_page', {'page': page})

# 通知函数已移动到 socket_utils.py 模块中
def notify_page_refresh(page_type, data=None):
    """通知特定页面刷新（兼容性函数）"""
    try:
        from socket_utils import notify_page_refresh as notify
        notify(page_type, data)
    except Exception as e:
        print(f"通知页面刷新失败: {e}")
        # 暂时忽略通知错误，不影响主要功能
        pass

# 使用独立的数据库工具模块
from db_utils import get_db, init_db

# 注册API蓝图
# 按照优先级逐步恢复API功能
# 1. 核心的团队成员管理API
from api.team import team_bp
from api.grades import grades_bp

# 2. 算法管理API
from api.algorithm import algorithm_bp

# 3. 创新项目和统计API
from api.innovation import innovation_bp
from api.innovation_project import innovation_project_bp
from api.advisor import advisor_bp
from api.notifications import notifications_bp
from api.research import research_bp  # 研究领域API
# from api.analytics import analytics_bp

# 注册所有API蓝图
app.register_blueprint(team_bp)  # 团队成员管理API
app.register_blueprint(grades_bp)  # 年级管理API
app.register_blueprint(algorithm_bp)  # 算法管理API
app.register_blueprint(innovation_bp)  # 创新统计和前端数据API
app.register_blueprint(innovation_project_bp)  # 创新项目API
app.register_blueprint(advisor_bp, url_prefix='/api')  # 指导老师API
app.register_blueprint(notifications_bp)  # 通知管理API
app.register_blueprint(research_bp)  # 研究领域API
# app.register_blueprint(analytics_bp, url_prefix='/api/analytics')  # 访问统计API

print("✅ 所有API蓝图已注册")

@app.before_request
def ensure_permanent_session():
    """确保会话持久化"""
    if session.get('username'):
        session.permanent = True

@app.before_request
def track_visits():
    """追踪页面访问 - 优化版本，减少数据库查询"""
    # 跳过以下路径的访问统计
    skip_paths = [
        '/static/', 
        '/api/', 
        '/favicon.ico',
        '/admin/login',  # 避免登录页面重复统计
    ]
    
    # 跳过POST请求和AJAX请求
    if request.method != 'GET':
        return
        
    # 跳过指定路径
    for path in skip_paths:
        if request.path.startswith(path):
            return
    
    # 跳过AJAX请求
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return
    
    # 为每个会话生成唯一ID
    if not session.get('session_id'):
        import uuid
        session['session_id'] = str(uuid.uuid4())
    
    # 使用异步方式记录访问，避免阻塞页面加载
    # try:
    #     from threading import Thread
    #     def async_record_visit():
    #         try:
    #             from api.analytics import record_visit
    #             record_visit(request.path)
    #         except Exception as e:
    #             print(f"异步访问统计记录失败: {e}")
    #     
    #     # 在后台线程中记录访问
    #     Thread(target=async_record_visit, daemon=True).start()
    # except Exception as e:
    #     # 访问统计失败不应影响正常页面访问
    #     print(f"访问统计线程启动失败: {e}")
    pass

@app.after_request
def add_header(response):
    """优化响应头 - 缓存和安全设置"""
    # 生产环境优化缓存
    if not app.debug:
        # 静态文件长期缓存
        if request.endpoint == 'static':
            response.cache_control.max_age = 31536000  # 1年
            response.cache_control.public = True
        # API响应短期缓存
        elif request.path.startswith('/api/'):
            response.cache_control.max_age = 300  # 5分钟
            response.cache_control.public = True
        # 页面缓存
        else:
            response.cache_control.max_age = 1800  # 30分钟
            response.cache_control.public = True
    else:
        # 开发环境禁用缓存
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    # 添加安全头部
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # 启用Gzip压缩提示
    response.headers['Vary'] = 'Accept-Encoding'
    
    return response

# 数据库操作辅助函数
def get_user_by_username(username):
    """根据用户名获取用户信息"""
    with get_db() as conn:
        return conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

def update_user(username, **kwargs):
    """更新用户信息"""
    with get_db() as conn:
        # 构建动态更新语句
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['display_name', 'avatar', 'password']:
                fields.append(f'{key} = ?')
                values.append(value)
        
        if fields:
            fields.append('updated_at = CURRENT_TIMESTAMP')
            values.append(username)
            query = f'UPDATE users SET {", ".join(fields)} WHERE username = ?'
            conn.execute(query, values)
            conn.commit()

def get_all_research_projects():
    """获取所有研究项目"""
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM research_projects ORDER BY order_index, created_at'
        ).fetchall()
        
        projects = []
        for row in rows:
            project = dict(row)
            # 解析JSON格式的成员列表
            if project['members']:
                try:
                    project['members'] = json.loads(project['members'])
                except:
                    project['members'] = []
            else:
                project['members'] = []
            projects.append(project)
        
        return projects

# 模拟数据（保持兼容性，实际数据从数据库读取）
projects_data = []
applications_data = []
team_data = []
research_data = []

# 实验室官网首页路由
@app.route('/')
def index():
    """实验室官网首页"""
    return render_template('frontend/index.html')

# 管理后台首页路由
@app.route('/admin')
def admin_index():
    """管理后台首页"""
    # 检查当前登录状态
    if 'username' in session:
        return redirect(url_for('admin_home_page'))
    
    # 检查自动登录标记和时间
    if session.get('auto_login_user') and session.get('auto_login_time'):
        auto_username = session.get('auto_login_user')
        auto_login_time = session.get('auto_login_time')
        
        # 检查是否在24小时内
        from datetime import datetime, timedelta
        try:
            login_time = datetime.fromisoformat(auto_login_time)
            if datetime.now() - login_time < timedelta(days=1):
                # 在24小时内，尝试自动登录
                user = get_user_by_username(auto_username)
                if user:
                    # 自动登录成功
                    session['username'] = auto_username
                    session['role'] = user['role']
                    session.permanent = True
                    # 更新自动登录时间
                    session['auto_login_time'] = datetime.now().isoformat()
                    return redirect(url_for('admin_home_page'))
                else:
                    # 用户不存在，清除标记
                    session.pop('auto_login_user', None)
                    session.pop('auto_login_time', None)
            else:
                # 超过24小时，清除标记
                session.pop('auto_login_user', None)
                session.pop('auto_login_time', None)
        except (ValueError, TypeError):
            # 时间格式错误，清除标记
            session.pop('auto_login_user', None)
            session.pop('auto_login_time', None)
    
    # 没有自动登录标记或已过期，跳转到登录页面
    return redirect(url_for('admin_login'))

# 前端展示首页路由
@app.route('/frontend')
def frontend_index():
    """前端展示首页"""
    return render_template('frontend/index.html')

# 新增后台页面路由
@app.route('/admin/home')
@require_auth
def admin_home_page():
    current_user = get_user_by_username(session['username'])
    display_name = current_user['display_name'] if current_user else session['username']
    avatar_url = current_user['avatar'] if current_user else ''
    
    return render_template('admin/home.html', 
                          username=display_name, 
                          display_name=display_name, 
                          avatar_url=avatar_url, 
                          active_nav='home')

# 前端获取指导老师数据的路由已移至 advisor_bp 中

# 前端获取科创成果数据的路由已移至 innovation_project_bp 中

# 前端页面路由
@app.route('/algorithm')
def algorithm():
    return render_template('frontend/algorithm.html')

@app.route('/test-api')
def test_api():
    return send_file('test_api.html')

@app.route('/matrix')
def matrix():
    return render_template('frontend/matrix.html')

@app.route('/blog-details')
def blog_details():
    return render_template('frontend/Blog details.html')

@app.route('/notification/<int:notification_id>')
def notification_detail(notification_id):
    """通知详情页面"""
    try:
        print(f"🔍 尝试加载通知详情: ID={notification_id}")
        
        with get_db() as conn:
            cursor = conn.execute('SELECT * FROM notifications WHERE id = ?', (notification_id,))
            notification = cursor.fetchone()
            
            print(f"📊 数据库查询结果: {notification is not None}")
            
            if not notification:
                print(f"❌ 通知不存在: ID={notification_id}")
                # 如果通知不存在，返回404页面或重定向到动态页面
                return redirect(url_for('dynamic'))
            
            print(f"📋 通知状态: {notification['status']}")
            
            # 仅允许已发布的通知访问
            if notification['status'] != 'published':
                print(f"❌ 通知未发布: ID={notification_id}, status={notification['status']}")
                return redirect(url_for('dynamic'))
                
            # 增加浏览量
            conn.execute('UPDATE notifications SET view_count = view_count + 1 WHERE id = ?', (notification_id,))
            conn.commit()
            
            # 将数据库行转换为字典
            notification_data = dict(notification)
            print(f"✅ 通知数据准备完成: {notification_data.get('title', 'Unknown')}")
            
            # 处理Markdown内容转换为HTML
            if notification_data.get('content'):
                try:
                    from api.notifications import markdown_to_html, is_markdown_content
                    content = notification_data['content']
                    
                    # 智能检测markdown内容并转换
                    if is_markdown_content(content):
                        notification_data['content'] = markdown_to_html(content)
                        print("📝 Markdown内容已转换")
                    # 如果不是markdown但包含HTML标签，直接使用
                    elif '<' in content and '>' in content:
                        print("📝 检测到HTML内容，直接使用")
                        pass  # 保持HTML内容不变
                    else:
                        # 简单文本格式化
                        content = content.replace('\n\n', '</p><p>')
                        content = content.replace('\n', '<br>')
                        notification_data['content'] = f'<p>{content}</p>'
                        print("📝 文本内容已格式化")
                except Exception as e:
                    print(f"⚠️ 内容处理出错: {e}")
                    # 如果处理失败，保持原内容
                    pass
            
            # 获取上一篇和下一篇通知（按order_index和publish_date排序，与API端点保持一致）
            # 处理order_index字段，如果为None则使用0
            order_index = notification_data.get('order_index', 0) or 0
            publish_date = notification_data.get('publish_date')
            
            # 获取上一篇（在列表中位置更靠前的：order_index更小的，或相同order_index但publish_date更新的）
            prev_cursor = conn.execute('''
                SELECT id, title, excerpt FROM notifications 
                WHERE status = 'published' AND (
                    (COALESCE(order_index, 0) < ? OR (COALESCE(order_index, 0) = ? AND publish_date > ?))
                )
                ORDER BY COALESCE(order_index, 0) DESC, publish_date ASC 
                LIMIT 1
            ''', (order_index, order_index, publish_date))
            prev_notification = prev_cursor.fetchone()
            
            # 获取下一篇（在列表中位置更靠后的：order_index更大的，或相同order_index但publish_date更早的）
            next_cursor = conn.execute('''
                SELECT id, title, excerpt FROM notifications 
                WHERE status = 'published' AND (
                    (COALESCE(order_index, 0) > ? OR (COALESCE(order_index, 0) = ? AND publish_date < ?))
                )
                ORDER BY COALESCE(order_index, 0) ASC, publish_date DESC 
                LIMIT 1
            ''', (order_index, order_index, publish_date))
            next_notification = next_cursor.fetchone()
            
            print(f"📄 导航链接: 上一篇={prev_notification is not None}, 下一篇={next_notification is not None}")
            
            # 处理发布日期格式化
            publish_date_str = ''
            pd = notification_data.get('publish_date')
            if pd:
                dt_obj = None
                try:
                    # 若为字符串，尝试解析为 datetime
                    if isinstance(pd, str):
                        try:
                            dt_obj = datetime.fromisoformat(pd)
                        except Exception:
                            try:
                                dt_obj = datetime.strptime(pd, '%Y-%m-%d %H:%M:%S')
                            except Exception:
                                dt_obj = None
                    else:
                        dt_obj = pd
                except Exception:
                    dt_obj = None
                
                if dt_obj:
                    publish_date_str = dt_obj.strftime('%Y年%m月%d日')
                else:
                    # 退化处理：仅取日期部分并做中文格式化
                    try:
                        date_part = str(pd).split(' ')[0]
                        y, m, d = date_part.split('-')
                        publish_date_str = f"{int(y)}年{int(m)}月{int(d)}日"
                    except Exception:
                        publish_date_str = str(pd)
            
            print(f"📅 发布日期: {publish_date_str}")
            print(f"🎯 准备渲染模板...")
            
            return render_template('frontend/notification_detail.html', 
                                 notification=notification_data, 
                                 publish_date_str=publish_date_str,
                                 prev_notification=dict(prev_notification) if prev_notification else None,
                                 next_notification=dict(next_notification) if next_notification else None)
    except Exception as e:
        print(f"❌ Error loading notification detail: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('dynamic'))

@app.route('/dynamic')
def dynamic():
    return render_template('frontend/dynamic.html')

@app.route('/introduction')
def introduction():
    return render_template('frontend/Introduction to the Laboratory.html')

@app.route('/charter')
def charter():
    return render_template('frontend/Laboratory Charter.html')

@app.route('/paper')
def paper():
    """论文页面"""
    try:
        papers = get_all_papers()
        return render_template('frontend/paper.html', papers=papers)
    except Exception as e:
        print(f"Error loading papers for frontend: {e}")
        return render_template('frontend/paper.html', papers=[])

@app.route('/project-recruitment')
def project_recruitment():
    return render_template('frontend/Project team recruitment.html')

@app.route('/algorithm-recruitment')
def algorithm_recruitment():
    return render_template('frontend/Recruitment for the Algorithm Group.html')

@app.route('/innovation')
def innovation():
    return render_template('frontend/science and technology innovation.html')

@app.route('/team')
def team():
    return render_template('frontend/team.html')






@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """后台管理登录页面"""
    # 检查当前登录状态
    if request.method == 'GET' and session.get('username'):
        return redirect(url_for('admin_home_page'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username and password:
            user = get_user_by_username(username)
            if user and check_password_hash(user['password'], password):
                session['username'] = username
                session['role'] = user['role']
                session.permanent = True
                
                # 设置自动登录标记和时间（24小时内有效）
                from datetime import datetime
                session['auto_login_user'] = username
                session['auto_login_time'] = datetime.now().isoformat()
                
                return redirect(url_for('admin_home_page'))
            else:
                return render_template('admin/login.html', error='用户名或密码错误')
        else:
            return render_template('admin/login.html', error='请输入用户名和密码')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """后台管理登出"""
    # 清除所有session数据，包括自动登录标记
    session.clear()
    return redirect(url_for('admin_login'))



# 新增后台页面路由
@app.route('/admin/team')
@require_auth
def admin_team_page():
    current_user = get_user_by_username(session['username'])
    display_name = current_user['display_name'] if current_user else session['username']
    avatar_url = current_user['avatar'] if current_user else ''
    
    return render_template('admin/team.html', 
                          username=display_name, 
                          display_name=display_name, 
                          avatar_url=avatar_url, 
                          active_nav='team')

@app.route('/admin/papers')
@require_auth
def admin_papers_page():
    current_user = get_user_by_username(session['username'])
    display_name = current_user['display_name'] if current_user else session['username']
    avatar_url = current_user['avatar'] if current_user else ''
    
    return render_template('admin/papers.html', 
                          username=display_name, 
                          display_name=display_name, 
                          avatar_url=avatar_url, 
                          active_nav='papers')

@app.route('/admin/innovation')
@require_auth
def admin_innovation_page():
    current_user = get_user_by_username(session['username'])
    display_name = current_user['display_name'] if current_user else session['username']
    avatar_url = current_user['avatar'] if current_user else ''
    
    return render_template('admin/innovation.html', 
                          username=display_name, 
                          display_name=display_name, 
                          avatar_url=avatar_url, 
                          active_nav='innovation')

@app.route('/admin/activities')
@require_auth
def admin_activities_page():
    current_user = get_user_by_username(session['username'])
    display_name = current_user['display_name'] if current_user else session['username']
    avatar_url = current_user['avatar'] if current_user else ''
    
    return render_template('admin/activities.html', 
                          username=display_name, 
                          display_name=display_name, 
                          avatar_url=avatar_url, 
                          active_nav='activities')

@app.route('/admin/algorithms')
@require_auth
def admin_algorithms_page():
    """算法管理页面"""
    current_user = get_user_by_username(session['username'])
    display_name = current_user['display_name'] if current_user else session['username']
    avatar_url = current_user['avatar'] if current_user else ''
    
    return render_template('admin/algorithms.html', 
                          username=display_name, 
                          display_name=display_name, 
                          avatar_url=avatar_url, 
                          active_nav='algorithms')

@app.route('/test/algorithms')
def test_algorithms_page():
    """算法管理测试页面"""
    return send_file('test_algorithms_page.html')

@app.route('/test/admin-api')
def test_admin_api_page():
    """管理后台API测试页面"""
    return send_file('test_admin_api.html')

@app.route('/debug/admin-simple')
def debug_admin_simple_page():
    """管理后台简单调试页面"""
    return send_file('debug_admin_simple.html')

@app.route('/test/frontend-data')
def test_frontend_data_page():
    """前端数据加载测试页面"""
    return send_file('test_frontend_data.html')

@app.route('/debug/frontend')
def debug_frontend_page():
    """前端数据加载调试页面"""
    return send_file('debug_frontend.html')

@app.route('/simple-test')
def simple_test_page():
    """简化测试页面"""
    return send_file('simple_test.html')

@app.route('/admin/algorithms-fixed')
def admin_algorithms_fixed():
    """修复版本的算法管理页面"""
    return render_template('admin/algorithms_fixed.html')

@app.route('/debug-admin')
def debug_admin():
    """管理后台调试页面"""
    return send_file('debug_admin_simple.html')

@app.route('/debug-algorithms')
def debug_algorithms():
    """算法管理调试页面"""
    return send_file('debug_algorithms.html')

@app.route('/test/innovation')
def test_innovation_page():
    """创新模块测试页面"""
    return send_file('test_innovation_page.html')

@app.route('/test/innovation-api')
def test_innovation_api_page():
    """创新模块API测试页面"""
    return send_file('test_innovation_api.html')

@app.route('/test/algorithms-api')
def test_algorithms_api_page():
    """算法管理API测试页面"""
    return send_file('test_algorithms_api.html')

# API接口
@app.route('/api/projects')
def get_projects():
    """获取项目数据API"""
    return jsonify(projects_data)

@app.route('/api/applications')
def get_applications():
    """获取申请数据API"""
    return jsonify(applications_data)

# 团队成员 API - 已移至 api/team.py Blueprint

# 前端活动数据API
@app.route('/api/frontend/activities')
def get_frontend_activities():
    """获取前端首页显示的活动数据（前3个）"""
    try:
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT id, title, excerpt, category, author, publish_date, reading_time, tags
                FROM notifications 
                WHERE status = 'published'
                ORDER BY order_index ASC, publish_date DESC
                LIMIT 3
            ''')
            activities = []
            for row in cursor.fetchall():
                activity = dict(row)
                # 格式化日期
                if activity['publish_date']:
                    try:
                        date_obj = datetime.strptime(activity['publish_date'], '%Y-%m-%d %H:%M:%S')
                        activity['formatted_date'] = date_obj.strftime('%Y.%m.%d')
                    except:
                        activity['formatted_date'] = activity['publish_date']
                else:
                    activity['formatted_date'] = '未知日期'
                activities.append(activity)
            return jsonify(activities)
    except Exception as e:
        print(f"Error fetching frontend activities: {e}")
        return jsonify([])

# 调试API - 查看所有通知数据


# 团队成员创建 API - 已移至 api/team.py Blueprint

# 团队成员更新 API - 已移至 api/team.py Blueprint

# 团队成员删除 API - 已移至 api/team.py Blueprint

# 团队成员排序 API - 已移至 api/team.py Blueprint

# 论文类别 API
@app.route('/api/paper-categories', methods=['GET'])
def get_paper_categories_api():
    """获取所有论文类别"""
    try:
        with get_db() as conn:
            rows = conn.execute('''
                SELECT id, name, level, description 
                FROM paper_categories 
                ORDER BY level, name
            ''').fetchall()
            
            categories = []
            for row in rows:
                categories.append({
                    'id': row['id'],
                    'name': row['name'],
                    'level': row['level'],
                    'description': row['description']
                })
            
            return jsonify(categories)
    except Exception as e:
        print(f"Error fetching paper categories: {e}")
        return jsonify([])

# 论文 API
@app.route('/api/papers', methods=['GET'])
def get_papers_api():
    """获取所有论文"""
    try:
        with get_db() as conn:
            # 获取所有论文
            cursor = conn.execute("SELECT * FROM papers ORDER BY order_index ASC, updated_at DESC")
            papers = cursor.fetchall()
            
            papers_data = []
            for paper in papers:
                paper_dict = dict(paper)
                
                # 从category_ids字段获取类别信息
                categories = paper_dict.get('category_ids', '[]')
                if isinstance(categories, str):
                    try:
                        categories = json.loads(categories)
                    except:
                        categories = []
                
                # 确保categories是列表格式
                if not isinstance(categories, list):
                    categories = []
                
                paper_dict['categories'] = categories
                
                # 处理authors字段，确保是列表格式
                authors = paper_dict.get('authors', '[]')
                if isinstance(authors, str):
                    try:
                        authors = json.loads(authors)
                    except:
                        authors = [authors] if authors else []
                
                if not isinstance(authors, list):
                    authors = [authors] if authors else []
                
                paper_dict['authors'] = authors
                
                papers_data.append(paper_dict)
            
            print(f"📚 返回论文数据: {len(papers_data)} 篇")
            print(f"📊 论文ID顺序: {[p['id'] for p in papers_data]}")
            return jsonify(papers_data)
    except Exception as e:
        print(f"Error fetching papers: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@app.route('/api/frontend/papers', methods=['GET'])
def get_frontend_papers_api():
    """获取论文数据用于前端展示（支持Vercel环境Mock数据）"""
    try:
        # 检查是否在 Vercel 环境中
        if os.environ.get('VERCEL'):
            # Vercel 环境：返回Mock数据
            mock_papers = [
                {
                    'id': 1,
                    'title': 'Deep Learning Approaches for Algorithm Optimization in Competitive Programming',
                    'authors': ['张伟教授', '李明博士', '王小红'],
                    'journal': 'IEEE Transactions on Software Engineering',
                    'year': 2024,
                    'abstract': '本文提出了一种基于深度学习的算法优化方法，专门针对程序设计竞赛中的复杂问题。通过分析历史竞赛数据，我们的方法能够自动识别最优算法策略。',
                    'categories': [16, 23],  # CCF-A, JCR一区
                    'status': 'published',
                    'pdf_url': 'https://example.com/paper1.pdf',
                    'code_url': 'https://github.com/acmlab/dl-optimization',
                    'citation_count': 15,
                    'doi': '10.1109/TSE.2024.001'
                },
                {
                    'id': 2,
                    'title': 'Novel Graph Algorithms for Social Network Analysis',
                    'authors': ['陈文华教授', '刘大鹏', '赵雪梅'],
                    'journal': 'Journal of Computer Science and Technology',
                    'year': 2024,
                    'abstract': '社交网络分析中的图算法研究，提出了一种新颖的社区发现算法，在大规模网络中具有良好的性能表现。',
                    'categories': [17, 20],  # CCF-B, 中科院二区
                    'status': 'published',
                    'pdf_url': 'https://example.com/paper2.pdf',
                    'code_url': '',
                    'citation_count': 8,
                    'doi': '10.1007/s11390-024-001'
                },
                {
                    'id': 3,
                    'title': 'Machine Learning-Based Code Completion for Programming Contests',
                    'authors': ['孙建国', '吴丽娟', '马志强'],
                    'journal': 'Software: Practice and Experience',
                    'year': 2023,
                    'abstract': '基于机器学习的代码自动补全系统，专为程序设计竞赛环境优化，显著提高了编程效率。',
                    'categories': [18, 21],  # CCF-C, 中科院三区
                    'status': 'published',
                    'pdf_url': '',
                    'code_url': 'https://github.com/acmlab/ml-codecomp',
                    'citation_count': 12,
                    'doi': '10.1002/spe.3245'
                },
                {
                    'id': 4,
                    'title': 'Efficient Parallel Algorithms for Large-Scale Data Processing',
                    'authors': ['黄志宇教授', '郑海龙博士'],
                    'journal': 'Parallel Computing',
                    'year': 2023,
                    'abstract': '针对大规模数据处理的并行算法研究，在MapReduce框架下实现了显著的性能提升。',
                    'categories': [24, 27],  # JCR二区, EI源刊
                    'status': 'published',
                    'pdf_url': 'https://example.com/paper4.pdf',
                    'code_url': '',
                    'citation_count': 22,
                    'doi': '10.1016/j.parco.2023.001'
                },
                {
                    'id': 5,
                    'title': 'Quantum Computing Applications in Cryptographic Algorithm Design',
                    'authors': ['钱学森', '冯诺依曼', '图灵'],
                    'journal': 'Nature Computational Science',
                    'year': 2024,
                    'abstract': '量子计算在密码学算法设计中的应用研究，探索了后量子时代的加密算法新方向。',
                    'categories': [16, 19],  # CCF-A, 中科院一区
                    'status': 'published',
                    'pdf_url': 'https://example.com/paper5.pdf',
                    'code_url': 'https://github.com/acmlab/quantum-crypto',
                    'citation_count': 35,
                    'doi': '10.1038/s43588-024-001'
                },
                {
                    'id': 6,
                    'title': 'Artificial Intelligence in Competitive Programming Education',
                    'authors': ['周恩来', '邓小平', '毛泽东'],
                    'journal': 'Computers & Education',
                    'year': 2023,
                    'abstract': '人工智能在程序设计竞赛教育中的应用，开发了智能化的训练平台和评测系统。',
                    'categories': [25, 28],  # JCR三区, EI会议
                    'status': 'published',
                    'pdf_url': '',
                    'code_url': 'https://github.com/acmlab/ai-education',
                    'citation_count': 6,
                    'doi': '10.1016/j.compedu.2023.001'
                }
            ]
            print(f"🔧 Vercel环境：返回论文Mock数据 {len(mock_papers)} 篇")
            return jsonify(mock_papers)
        
        # 本地环境：正常数据库查询
        return get_papers_api()
    except Exception as e:
        print(f"Error in get_frontend_papers_api: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

# 前端获取指导老师数据的路由已移至 advisor_bp 中

# 前端获取科创成果数据的路由已移至 innovation_project_bp 中

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 在开发环境中启动应用
    is_debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    if is_vercel:
        # 在Vercel环境中，应用由Vercel管理，不需要run()
        print("🚀 在Vercel环境中运行")
    else:
        # 本地开发环境
        print("🚀 启动本地开发服务器")
        try:
            socketio.run(app, 
                        debug=is_debug, 
                        host='0.0.0.0', 
                        port=int(os.environ.get('PORT', 5000)),
                        allow_unsafe_werkzeug=True)
        except Exception as e:
            print(f"⚠️ SocketIO启动失败，使用普通Flask启动: {e}")
            app.run(debug=is_debug, 
                   host='0.0.0.0', 
                   port=int(os.environ.get('PORT', 5000)))
