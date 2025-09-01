# 公共工具函数模块
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# 允许的图片文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """检查文件是否为允许的图片类型"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(original_filename, prefix="file"):
    """生成唯一的文件名"""
    if not original_filename:
        return None
    
    name, ext = os.path.splitext(secure_filename(original_filename))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_suffix = os.urandom(4).hex()
    return f"{prefix}_{timestamp}_{random_suffix}{ext}"

def ensure_upload_dir(upload_type, file):
    """确保上传目录存在并保存文件
    
    Args:
        upload_type (str): 上传类型，如 'carousel', 'training_projects' 等
        file: 上传的文件对象
    
    Returns:
        str: 保存后的文件名
    """
    # 创建上传目录
    upload_dir = os.path.join('static', 'uploads', upload_type)
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    filename = generate_unique_filename(file.filename, upload_type)
    
    # 保存文件
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    return filename 