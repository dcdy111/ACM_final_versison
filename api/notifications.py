from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
import sqlite3
import json
import markdown
from datetime import datetime
from werkzeug.security import check_password_hash
import tempfile
import re
from socket_utils import notify_page_refresh

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

# 允许的文档文件扩展名（只保留Markdown）
ALLOWED_DOC_EXTENSIONS = {'md', 'markdown'}

def allowed_doc_file(filename):
    if '.' not in filename:
        return False
    file_parts = filename.rsplit('.', 1)
    if len(file_parts) < 2:
        return False
    return file_parts[1].lower() in ALLOWED_DOC_EXTENSIONS

def ensure_upload_dir():
    """确保上传目录存在"""
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'notifications')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    return upload_dir

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(current_app.config.get('DATABASE', 'acm_lab.db'))
    conn.row_factory = sqlite3.Row
    return conn

def require_auth():
    """验证用户权限"""
    # 这里简化处理，实际项目中应该有完整的权限验证
    return True

def markdown_to_html(content):
    """将Markdown内容转换为HTML"""
    try:
        import re
        
        # 预处理：处理图片链接，确保相对路径正确
        content = preprocess_markdown_images(content)
        
        # 配置markdown扩展
        md = markdown.Markdown(extensions=[
            'extra',  # 支持表格、代码块等
            'codehilite',  # 代码高亮
            'toc',  # 目录生成
            'nl2br',  # 换行转换
            'tables',  # 表格支持
            'fenced_code',  # 代码块支持
            'attr_list',  # 属性列表支持
        ], extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': False,
                'noclasses': True
            },
            'toc': {
                'anchorlink': True,
                'title': '目录'
            }
        })
        
        html_content = md.convert(content)
        
        # 优化HTML内容
        html_content = optimize_html_content(html_content)
        
        return html_content
    except Exception as e:
        print(f"Markdown转HTML错误: {e}")
        return content

def preprocess_markdown_images(content):
    """预处理markdown中的图片链接"""
    import re
    
    # 处理相对路径的图片，确保路径正确
    def replace_image(match):
        alt_text = match.group(1)
        image_path = match.group(2)
        title = match.group(3) if match.group(3) else ""
        
        # 如果是相对路径且不是以/static开头，添加static路径前缀
        if not image_path.startswith(('http://', 'https://', '/static/', 'data:')):
            if image_path.startswith('uploads/'):
                image_path = f'/static/{image_path}'
            elif not image_path.startswith('/'):
                image_path = f'/static/uploads/notifications/images/{image_path}'
        
        # 添加图片的CSS类和懒加载属性
        if title:
            return f'![{alt_text}]({image_path} "{title}"){{.responsive-image loading="lazy"}}'
        else:
            return f'![{alt_text}]({image_path}){{.responsive-image loading="lazy"}}'
    
    # 匹配markdown图片语法：![alt](src "title")
    pattern = r'!\[([^\]]*)\]\(([^\)]+?)(?:\s+"([^"]*)")?\)'
    content = re.sub(pattern, replace_image, content)
    
    return content

def optimize_html_content(html_content):
    """优化HTML内容的排版和样式"""
    import re
    
    # 为标题添加锚点
    def add_header_anchors(match):
        level = len(match.group(1))
        content = match.group(2)
        anchor_id = re.sub(r'[^\w\u4e00-\u9fff]+', '-', content).strip('-').lower()
        return f'<h{level} id="{anchor_id}">{content}</h{level}>'
    
    html_content = re.sub(r'<h([1-6])>(.*?)</h[1-6]>', add_header_anchors, html_content)
    
    # 为表格添加响应式包装
    html_content = re.sub(
        r'<table>', 
        '<div class="table-responsive"><table class="table table-striped">', 
        html_content
    )
    html_content = re.sub(r'</table>', '</table></div>', html_content)
    
    # 为代码块添加复制按钮容器
    html_content = re.sub(
        r'<pre><code(.*?)>', 
        r'<div class="code-block-container"><pre><code\1>', 
        html_content
    )
    html_content = re.sub(r'</code></pre>', '</code></pre></div>', html_content)
    
    # 为图片添加懒加载和灯箱效果
    def enhance_image_tag(match):
        before_src = match.group(1)
        src = match.group(2)
        after_src = match.group(3)
        
        # 检查是否已经有这些属性
        full_tag = f'<img{before_src}src="{src}"{after_src}>'
        
        # 如果没有loading属性，添加它
        if 'loading=' not in full_tag:
            after_src += ' loading="lazy"'
        
        # 如果没有responsive-image类，添加它
        if 'responsive-image' not in full_tag:
            if 'class=' in full_tag:
                # 如果已有class属性，添加到现有class中
                after_src = re.sub(r'class="([^"]*)"', r'class="\1 responsive-image"', after_src)
            else:
                # 如果没有class属性，添加新的class
                after_src += ' class="responsive-image"'
        
        # 如果没有onclick属性，添加它
        if 'onclick=' not in full_tag:
            after_src += ' onclick="openImageModal(this)"'
        
        # 如果没有cursor样式，添加它
        if 'cursor:' not in full_tag:
            if 'style=' in full_tag:
                # 如果已有style属性，添加到现有style中
                after_src = re.sub(r'style="([^"]*)"', r'style="\1; cursor: pointer;"', after_src)
            else:
                # 如果没有style属性，添加新的style
                after_src += ' style="cursor: pointer;"'
        
        return f'<img{before_src}src="{src}"{after_src}>'
    
    html_content = re.sub(
        r'<img([^>]*?)src="([^"]*?)"([^>]*?)>', 
        enhance_image_tag, 
        html_content
    )
    
    # 为引用块添加样式类
    html_content = re.sub(r'<blockquote>', '<blockquote class="blockquote">', html_content)
    
    # 处理段落间距
    html_content = re.sub(r'<p></p>', '', html_content)
    
    return html_content

@notifications_bp.route('', methods=['GET'])
def get_notifications():
    """获取通知列表"""
    try:
        conn = get_db()
        cursor = conn.execute('''
            SELECT * FROM notifications 
            ORDER BY order_index ASC, publish_date DESC
        ''')
        notifications = [dict(row) for row in cursor.fetchall()]
        return jsonify(notifications)
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return jsonify({"error": "获取通知列表失败"}), 500

@notifications_bp.route('/<int:notification_id>', methods=['GET'])
def get_notification(notification_id):
    """获取通知详情"""
    try:
        conn = get_db()
        notification = conn.execute('''
            SELECT id, title, content, raw_content, excerpt, author, category, 
                   reading_time, tags, status, source_type, source_file, 
                   word_count, view_count, card_style, publish_date, created_at, updated_at
            FROM notifications 
            WHERE id = ?
        ''', (notification_id,)).fetchone()
        
        if not notification:
            return jsonify({"error": "通知不存在"}), 404
        
        # 转换为字典
        notification_dict = dict(notification)
        
        # 增加浏览量
        conn.execute('UPDATE notifications SET view_count = view_count + 1 WHERE id = ?', (notification_id,))
        conn.commit()
        
        return jsonify(notification_dict), 200
        
    except Exception as e:
        print(f"Error getting notification: {e}")
        return jsonify({"error": "获取通知详情失败"}), 500

@notifications_bp.route('', methods=['POST'])
def create_notification():
    """创建新通知"""
    if not require_auth():
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('title') or not data.get('content'):
            return jsonify({"error": "标题和内容不能为空"}), 400
        
        # 处理内容 - 检测是否为markdown格式
        raw_content = data['content']
        
        # 如果内容包含markdown语法，转换为HTML
        if is_markdown_content(raw_content):
            html_content = markdown_to_html(raw_content)
        else:
            html_content = raw_content
            raw_content = html_content  # 如果不是markdown，原始内容就是HTML
        
        # 自动生成摘要（如果未提供）
        excerpt = data.get('excerpt') or auto_generate_excerpt(html_content)
        
        # 计算阅读时间
        reading_time = data.get('reading_time') or calculate_reading_time(html_content)
        
        # 计算字数
        word_count = len(html_content)
        
        # 处理卡片样式配置
        card_style = data.get('card_style', '')
        
        conn = get_db()
        cursor = conn.execute('''
            INSERT INTO notifications (
                title, content, raw_content, excerpt, author, category, reading_time, 
                tags, status, source_type, word_count, card_style, publish_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['title'],
            html_content,
            raw_content,
            excerpt,
            data.get('author', 'ACM算法研究实验室'),
            data.get('category', '实验室制度'),
            reading_time,
            data.get('tags', ''),
            data.get('status', 'published'),
            data.get('source_type', 'online'),
            word_count,
            card_style,
            datetime.now()
        ))
        
        notification_id = cursor.lastrowid
        conn.commit()
        
        # 通知前端刷新动态页面
        notify_page_refresh('dynamic', {'created': True, 'notification_id': notification_id})
        
        return jsonify({"id": notification_id, "message": "通知创建成功"}), 201
        
    except Exception as e:
        print(f"Error creating notification: {e}")
        return jsonify({"error": "创建通知失败"}), 500

def is_markdown_content(content):
    """检测内容是否包含markdown语法"""
    import re
    
    # 检测常见的markdown标记
    markdown_patterns = [
        r'^#+\s',  # 标题
        r'\*\*.*?\*\*',  # 粗体
        r'\*.*?\*',  # 斜体
        r'`.*?`',  # 行内代码
        r'```[\s\S]*?```',  # 代码块
        r'^\s*[-*+]\s',  # 无序列表
        r'^\s*\d+\.\s',  # 有序列表
        r'^\s*>',  # 引用
        r'\[.*?\]\(.*?\)',  # 链接
        r'!\[.*?\]\(.*?\)',  # 图片
        r'\|.*?\|',  # 表格
        r'^---+$',  # 分隔线
    ]
    
    for pattern in markdown_patterns:
        if re.search(pattern, content, re.MULTILINE):
            return True
    
    return False

@notifications_bp.route('/<int:notification_id>', methods=['PUT'])
def update_notification(notification_id):
    """更新通知"""
    if not require_auth():
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('title') or not data.get('content'):
            return jsonify({"error": "标题和内容不能为空"}), 400
        
        # 处理内容 - 检测是否为markdown格式
        raw_content = data['content']
        
        # 如果内容包含markdown语法，转换为HTML
        if is_markdown_content(raw_content):
            html_content = markdown_to_html(raw_content)
        else:
            html_content = raw_content
            raw_content = html_content  # 如果不是markdown，原始内容就是HTML
        
        # 自动生成摘要（如果未提供）
        excerpt = data.get('excerpt') or auto_generate_excerpt(html_content)
        
        # 计算阅读时间
        reading_time = data.get('reading_time') or calculate_reading_time(html_content)
        
        # 计算字数
        word_count = len(html_content)
        
        # 处理卡片样式配置
        card_style = data.get('card_style', '')
        
        conn = get_db()
        
        # 检查通知是否存在
        existing = conn.execute('SELECT id FROM notifications WHERE id = ?', (notification_id,)).fetchone()
        if not existing:
            return jsonify({"error": "通知不存在"}), 404
        
        # 更新通知
        conn.execute('''
            UPDATE notifications 
            SET title = ?, content = ?, raw_content = ?, excerpt = ?, 
                author = ?, category = ?, reading_time = ?, tags = ?, 
                status = ?, word_count = ?, card_style = ?, updated_at = ?
            WHERE id = ?
        ''', (
            data['title'],
            html_content,
            raw_content,
            excerpt,
            data.get('author', 'ACM算法研究实验室'),
            data.get('category', '实验室制度'),
            reading_time,
            data.get('tags', ''),
            data.get('status', 'published'),
            word_count,
            card_style,
            datetime.now(),
            notification_id
        ))
        
        conn.commit()
        
        # 通知前端刷新动态页面
        notify_page_refresh('dynamic', {'updated': True, 'notification_id': notification_id})
        
        return jsonify({"message": "通知更新成功"}), 200
        
    except Exception as e:
        print(f"Error updating notification: {e}")
        return jsonify({"error": "更新通知失败"}), 500

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """删除通知"""
    if not require_auth():
        return jsonify({"error": "未授权"}), 401
    
    try:
        conn = get_db()
        
        # 检查通知是否存在
        cursor = conn.execute('SELECT id, source_file FROM notifications WHERE id = ?', (notification_id,))
        notification = cursor.fetchone()
        
        if not notification:
            return jsonify({"error": "通知不存在"}), 404
        
        # 删除关联的上传文件记录
        conn.execute('DELETE FROM uploaded_files WHERE notification_id = ?', (notification_id,))
        
        # 删除通知
        conn.execute('DELETE FROM notifications WHERE id = ?', (notification_id,))
        conn.commit()
        
        # 如果有源文件，尝试删除
        if notification['source_file']:
            try:
                file_path = os.path.join(current_app.root_path, 'static', notification['source_file'])
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"删除源文件失败: {e}")
        
        # 通知前端刷新动态页面
        notify_page_refresh('dynamic', {'deleted': True, 'notification_id': notification_id})
        
        return jsonify({"message": "通知删除成功"})
        
    except Exception as e:
        print(f"Error deleting notification: {e}")
        return jsonify({"error": "删除通知失败"}), 500

@notifications_bp.route('/reorder', methods=['POST'])
def reorder_notifications():
    """重新排序通知"""
    if not require_auth():
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        notification_ids = data.get('notification_ids', [])
        
        if not notification_ids:
            return jsonify({"error": "无效的排序数据"}), 400
        
        conn = get_db()
        
        # 更新排序
        for index, notification_id in enumerate(notification_ids):
            conn.execute(
                'UPDATE notifications SET order_index = ?, updated_at = ? WHERE id = ?',
                (index, datetime.now(), notification_id)
            )
        
        conn.commit()
        
        # 通知前端刷新动态页面
        notify_page_refresh('dynamic', {'reordered': True})
        
        return jsonify({"message": "排序保存成功"})
        
    except Exception as e:
        print(f"Error reordering notifications: {e}")
        return jsonify({"error": "保存排序失败"}), 500

@notifications_bp.route('/upload', methods=['POST'])
def upload_document():
    """上传文档并自动处理"""
    if not require_auth():
        return jsonify({"error": "未授权"}), 401
    
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({"error": "未选择文件"}), 400
        
        file = request.files['file']
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '实验室制度')
        
        if not file or file.filename == '':
            return jsonify({"error": "未选择文件"}), 400
        
        if not title:
            return jsonify({"error": "标题不能为空"}), 400
        
        if not allowed_doc_file(file.filename):
            return jsonify({"error": "不支持的文件类型"}), 400
        
        # 保存文件
        upload_dir = ensure_upload_dir()
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # 获取文件类型
        if '.' not in filename:
            return jsonify({"error": "文件名必须包含扩展名"}), 400
        
        file_parts = filename.rsplit('.', 1)
        if len(file_parts) < 2:
            return jsonify({"error": "无效的文件格式"}), 400
        
        file_type = file_parts[1].lower()
        
        # 处理文档内容（只支持Markdown）
        print(f"开始处理Markdown文档")
        content = extract_text_from_markdown(file_path)
        
        if not content:
            # 清理上传的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"error": "文档内容解析失败，请检查文件格式或内容"}), 400
        
        # 处理内容格式
        raw_content = content
        html_content = markdown_to_html(content)
        
        # 生成摘要和计算阅读时间
        excerpt = auto_generate_excerpt(html_content)
        reading_time = calculate_reading_time(html_content)
        word_count = len(html_content)
        
        # 处理卡片样式配置（从表单数据获取，如果有的话）
        card_style = request.form.get('card_style', '')
        
        # 保存到数据库
        conn = get_db()
        cursor = conn.execute('''
            INSERT INTO notifications (
                title, content, raw_content, excerpt, author, category, reading_time,
                status, source_type, source_file, word_count, card_style, publish_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title,
            html_content,
            raw_content,
            excerpt,
            'ACM算法研究实验室',
            category,
            reading_time,
            'published',
            'upload',
            f'uploads/notifications/{unique_filename}',
            word_count,
            card_style,
            datetime.now()
        ))
        
        notification_id = cursor.lastrowid
        
        # 记录上传文件信息
        conn.execute('''
            INSERT INTO uploaded_files (
                stored_filename, original_filename, file_size, notification_id, upload_status
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            unique_filename,
            filename,
            os.path.getsize(file_path),
            notification_id,
            'success'
        ))
        
        conn.commit()
        
        return jsonify({
            "id": notification_id,
            "message": "文档上传处理成功",
            "word_count": word_count,
            "reading_time": reading_time
        }), 201
        
    except Exception as e:
        print(f"Error uploading document: {e}")
        # 清理可能的临时文件
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": "文档上传处理失败"}), 500 

@notifications_bp.route('/upload_image', methods=['POST'])
def upload_image():
    """上传图片用于markdown编辑器"""
    if not require_auth():
        return jsonify({"error": "未授权"}), 401
    
    try:
        if 'image' not in request.files:
            return jsonify({"error": "没有选择图片"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "没有选择图片"}), 400
        
        # 检查文件类型
        if not allowed_image_file(file.filename):
            return jsonify({"error": "不支持的图片格式"}), 400
        
        # 生成唯一文件名
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"img_{uuid.uuid4().hex}{ext}"
        
        # 确保上传目录存在
        upload_dir = ensure_upload_dir()
        images_dir = os.path.join(upload_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        file_path = os.path.join(images_dir, unique_filename)
        
        # 保存文件
        file.save(file_path)
        
        # 返回图片URL
        image_url = f'/static/uploads/notifications/images/{unique_filename}'
        
        return jsonify({
            'success': True,
            'url': image_url,
            'filename': unique_filename,
            'message': '图片上传成功'
        })
        
    except Exception as e:
        print(f"Error uploading image: {e}")
        return jsonify({"error": "图片上传失败"}), 500

def allowed_image_file(filename):
    """检查是否为允许的图片文件"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'}

@notifications_bp.route('/upload_card_image', methods=['POST'])
def upload_card_image():
    """上传卡片背景图片"""
    if not require_auth():
        return jsonify({"error": "未授权"}), 401
    
    try:
        if 'image' not in request.files:
            return jsonify({"error": "没有选择图片"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "没有选择图片"}), 400
        
        # 检查文件类型
        if not allowed_image_file(file.filename):
            return jsonify({"error": "不支持的图片格式"}), 400
        
        # 生成唯一文件名
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"card_{uuid.uuid4().hex}{ext}"
        
        # 确保上传目录存在
        upload_dir = ensure_upload_dir()
        cards_dir = os.path.join(upload_dir, 'cards')
        os.makedirs(cards_dir, exist_ok=True)
        
        file_path = os.path.join(cards_dir, unique_filename)
        
        # 保存文件
        file.save(file_path)
        
        # 返回图片URL
        image_url = f'/static/uploads/notifications/cards/{unique_filename}'
        
        return jsonify({
            'success': True,
            'url': image_url,
            'filename': unique_filename,
            'message': '卡片背景图片上传成功'
        })
        
    except Exception as e:
        print(f"Error uploading card image: {e}")
        return jsonify({"error": "卡片背景图片上传失败"}), 500 

def extract_text_from_markdown(file_path):
    """从Markdown文件提取文本"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Markdown解析错误: {e}")
        return None

def is_markdown_content(content):
    """检测内容是否包含Markdown语法"""
    if not content:
        return False
    
    # 检查常见的Markdown语法
    markdown_patterns = [
        r'^#{1,6}\s',  # 标题
        r'\*\*.*?\*\*',  # 粗体
        r'\*.*?\*',  # 斜体
        r'`.*?`',  # 行内代码
        r'```[\s\S]*?```',  # 代码块
        r'^\s*[-*+]\s',  # 无序列表
        r'^\s*\d+\.\s',  # 有序列表
        r'\[.*?\]\(.*?\)',  # 链接
        r'!\[.*?\]\(.*?\)',  # 图片
        r'^\s*>\s',  # 引用
        r'^\|.*\|$',  # 表格
        r'^\s*---+\s*$',  # 分割线
    ]
    
    for pattern in markdown_patterns:
        if re.search(pattern, content, re.MULTILINE):
            return True
    
    return False

def auto_generate_excerpt(content, max_length=200):
    """自动生成摘要"""
    if not content:
        return ""
    
    # 移除Markdown标记
    text = re.sub(r'[#*`_~\[\]()]', '', content)
    text = re.sub(r'\n+', ' ', text)
    text = text.strip()
    
    if len(text) <= max_length:
        return text
    
    # 尝试在句号处截断
    sentences = text.split('。')
    excerpt = ""
    for sentence in sentences:
        if len(excerpt + sentence + '。') <= max_length:
            excerpt += sentence + '。'
        else:
            break
    
    if not excerpt:
        excerpt = text[:max_length] + '...'
    
    return excerpt

def calculate_reading_time(content):
    """计算阅读时间（按300字/分钟）"""
    if not content:
        return 1
    
    # 计算字数（中文字符+英文单词）
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', content))
    
    total_chars = chinese_chars + english_words
    reading_time = max(1, round(total_chars / 300))
    
    return reading_time 